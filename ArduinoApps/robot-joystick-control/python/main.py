"""
Robot Joystick Control - Main Application
Orchestrates controllers (Manual, PID, IA) and handles WebSocket communication.
"""
import os
import json
from arduino.app_utils import App, Bridge, Logger
from arduino.app_bricks.web_ui import WebUI

from controllers import ManualController, PIDController, IAController, AutotuneController
from utils import Recorder

# --- Initialization ---
logger = Logger("robot-joystick-control")
web_ui = WebUI()

# --- Paths ---
DIR_PYTHON = os.path.dirname(os.path.abspath(__file__))
DIR_DATA = os.path.join(DIR_PYTHON, 'data')
PID_CONFIG_PATH = os.path.join(DIR_DATA, 'pid_config.json')

# --- Helper: Load/Save PID Config ---
def load_pid_config():
    if os.path.exists(PID_CONFIG_PATH):
        try:
            with open(PID_CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_pid_config(params):
    try:
        with open(PID_CONFIG_PATH, 'w') as f:
            json.dump(params, f, indent=4)
    except Exception as e:
        logger.warning(f"Error guardando PID config: {e}")

# Load initial config
initial_pid_params = load_pid_config() or {
    "setpoint": 15.0, "kp": 2.0, "ki": 0.1, "kd": 0.5, "base_speed": 100
}

# --- Controllers ---
controllers = {
    "manual": ManualController(),
    "pid": PIDController(**initial_pid_params),
    "ia": IAController(data_dir=DIR_DATA),
    "autotune": AutotuneController(setpoint=initial_pid_params["setpoint"])
}

# Active mode and controller
active_mode = "manual"
active_controller = controllers["manual"]

# --- Recorder ---
recorder = Recorder(data_dir=DIR_DATA)

# --- State ---
ultimo_pwm_izq = 0
ultimo_pwm_der = 0
pid_active = False  # New state for PID activation

# Log startup info
logger.info(f"Directorio de datos: {DIR_DATA}")
logger.info(f"Modelo IA disponible: {controllers['ia'].is_available()}")
logger.info(f"Archivo de grabación: {recorder.get_filepath()}")


def set_mode(mode: str) -> bool:
    """
    Switch to a different control mode.
    
    Args:
        mode: One of 'manual', 'pid', 'ia'
        
    Returns:
        True if mode was changed successfully
    """
    global active_mode, active_controller
    
    if mode not in controllers:
        logger.warning(f"Modo desconocido: {mode}")
        return False
    
    # Check IA availability
    if mode == "ia" and not controllers["ia"].is_available():
        logger.error("Modelo IA no disponible")
        web_ui.send_message("status", {
            "message": "Error: Modelo IA no disponible. Entrena el modelo primero."
        })
        return False
    
    # Deactivate current controller
    active_controller.on_deactivate()
    
    # Stop motors when switching modes
    Bridge.notify("detener")
    
    # Switch to new controller
    active_mode = mode
    active_controller = controllers[mode]
    active_controller.on_activate()
    
    # Reset PID activation when switching
    global pid_active
    pid_active = False
    
    logger.info(f"Modo cambiado a: {mode}")
    web_ui.send_message("mode_changed", {"mode": mode})
    web_ui.send_message("status", {"message": f"Modo: {mode.upper()}"})
    
    return True


def al_recibir_distancias(d_frontal: float, d_derecho: float):
    """
    Callback for sensor data from Arduino.
    Processes data through active controller and sends commands.
    """
    global ultimo_pwm_izq, ultimo_pwm_der, pid_active
    
    # Send sensor data to UI
    try:
        web_ui.send_message("sensores", {
            "frontal": round(d_frontal, 1),
            "derecho": round(d_derecho, 1)
        })
    except Exception as e:
        logger.warning(f"Error enviando sensores al UI: {e}")
    
    # Process through active controller (only for autonomous modes)
    if active_mode in ("pid", "ia", "autotune"):
        # If in PID mode, only compute if active
        if active_mode == "pid" and not pid_active:
            return

        try:
            pwm_izq, pwm_der = active_controller.compute(d_frontal, d_derecho)
            ultimo_pwm_izq, ultimo_pwm_der = pwm_izq, pwm_der
            
            # Send to Arduino (using notify to avoid timeouts at 50Hz)
            Bridge.notify("motores", pwm_izq, pwm_der)
            
            # Update UI
            web_ui.send_message("motores", {
                "izquierdo": pwm_izq,
                "derecho": pwm_der
            })

            # Check if autotune finished
            if active_mode == "autotune":
                results = active_controller.get_results()
                web_ui.send_message("autotune_progress", results)
                
                if results["finished"]:
                    # Update PID parameters
                    controllers["pid"].set_parameters(
                        kp=results["kp"],
                        ki=results["ki"],
                        kd=results["kd"]
                    )
                    # Save permanent config
                    save_pid_config(controllers["pid"].get_parameters())
                    
                    logger.info(f"Auto-calibración completada: {results}")
                    web_ui.send_message("status", {"message": "Auto-calibración COMPLETADA"})
                    
                    # Switch back to PID mode (but inactive)
                    set_mode("pid")
        except Exception as e:
            logger.warning(f"Error en controlador {active_mode}: {e}")
    
    # Record data if recording is active
    if recorder.is_recording():
        recorder.record(d_frontal, d_derecho, ultimo_pwm_izq, ultimo_pwm_der)


def on_joystick_move(sid, data):
    """Handle joystick input from frontend."""
    global ultimo_pwm_izq, ultimo_pwm_der
    
    # Only process in manual mode
    if active_mode != "manual":
        return
    
    x = data.get("x", 0)
    y = data.get("y", 0)
    
    manual = controllers["manual"]
    pwm_izq, pwm_der = manual.process_joystick(x, y)
    ultimo_pwm_izq, ultimo_pwm_der = pwm_izq, pwm_der
    
    try:
        Bridge.notify("joystick", x, y)
        web_ui.send_message("motores", {
            "izquierdo": pwm_izq,
            "derecho": pwm_der
        })
    except Exception as e:
        logger.warning(f"Error en joystick: {e}")


def on_girar(sid, data):
    """Handle turn button input from frontend."""
    global ultimo_pwm_izq, ultimo_pwm_der
    
    # Only process in manual mode
    if active_mode != "manual":
        return
    
    direccion = data.get("dir")
    accion = data.get("action")
    
    manual = controllers["manual"]
    pwm_izq, pwm_der = manual.process_turn(direccion, accion)
    ultimo_pwm_izq, ultimo_pwm_der = pwm_izq, pwm_der
    
    try:
        if accion == "stop":
            Bridge.notify("detener")
        elif direccion == "izq":
            Bridge.notify("girar_izq")
        elif direccion == "der":
            Bridge.notify("girar_der")
        
        web_ui.send_message("motores", {
            "izquierdo": pwm_izq,
            "derecho": pwm_der
        })
    except Exception as e:
        logger.warning(f"Error en giro: {e}")


def on_change_mode(sid, data):
    """Handle mode change request from frontend."""
    mode = data.get("mode", "manual")
    set_mode(mode)


def on_toggle_recording(sid, data):
    """Handle recording toggle from frontend."""
    active = data.get("active", False)
    recorder.toggle(active)
    estado = "INICIADA" if recorder.is_recording() else "DETENIDA"
    logger.info(f"Grabación: {estado}")
    web_ui.send_message("status", {"message": f"Grabación {estado}"})


def on_pid_params(sid, data):
    """Handle PID parameter update from frontend."""
    pid = controllers["pid"]
    pid.set_parameters(
        setpoint=data.get("setpoint"),
        kp=data.get("kp"),
        ki=data.get("ki"),
        kd=data.get("kd"),
        base_speed=data.get("base_speed")
    )
    # Update autotune setpoint too
    controllers["autotune"].setpoint = pid.setpoint
    
    save_pid_config(pid.get_parameters())
    logger.info(f"PID params actualizados: {pid.get_parameters()}")
    web_ui.send_message("status", {"message": "Parámetros PID actualizados"})


def on_toggle_pid(sid, data):
    """Handle PID activation toggle."""
    global pid_active
    pid_active = data.get("active", False)
    estado = "ACTIVADO" if pid_active else "DESACTIVADO"
    logger.info(f"PID: {estado}")
    web_ui.send_message("pid_status", {"active": pid_active})
    
    if not pid_active:
        # Stop motors if deactivated
        Bridge.notify("detener")
        web_ui.send_message("motores", {"izquierdo": 0, "derecho": 0})


# --- Register callbacks ---
Bridge.provide("distancias", al_recibir_distancias)
web_ui.on_message("joystick", on_joystick_move)
web_ui.on_message("girar", on_girar)
web_ui.on_message("change_mode", on_change_mode)
web_ui.on_message("toggle_recording", on_toggle_recording)
web_ui.on_message("pid_params", on_pid_params)
web_ui.on_message("toggle_pid", on_toggle_pid)


@web_ui.on_connect
def on_connect(sid):
    """Handle new client connection."""
    logger.info(f"Cliente conectado: {sid}")
    
    # Send current state to new client
    web_ui.send_message("status", {"message": "Conectado al robot"})
    web_ui.send_message("mode_changed", {"mode": active_mode})
    web_ui.send_message("pid_params", controllers["pid"].get_parameters())
    web_ui.send_message("ia_available", {"available": controllers["ia"].is_available()})


if __name__ == "__main__":
    logger.info("Iniciando Robot Joystick Control (Modular)...")
    logger.info(f"Modos disponibles: {list(controllers.keys())}")
    App.run()
