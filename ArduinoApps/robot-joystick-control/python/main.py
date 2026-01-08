"""
Robot Joystick Control - Main Application
Orchestrates controllers (Manual, Auto) and handles WebSocket communication.
"""
import os
from arduino.app_utils import App, Bridge, Logger
from arduino.app_bricks.web_ui import WebUI

from controllers import ManualController, AutoController

# --- Initialization ---
logger = Logger("robot-joystick-control")
web_ui = WebUI()

# --- Controllers ---
controllers = {
    "manual": ManualController(),
    "auto": AutoController()
}

# Active mode and controller
active_mode = "manual"
active_controller = controllers["manual"]

# --- State ---
ultimo_pwm_izq = 0
ultimo_pwm_der = 0
auto_active = False  # State for auto controller activation
ciclos_ui = 0        # Counter to throttle UI updates

# Log startup info
logger.info("Controladores disponibles: manual, auto")


def set_mode(mode: str) -> bool:
    """
    Switch to a different control mode.

    Args:
        mode: One of 'manual', 'auto'

    Returns:
        True if mode was changed successfully
    """
    global active_mode, active_controller, auto_active

    if mode not in controllers:
        logger.warning(f"Modo desconocido: {mode}")
        return False

    # Deactivate current controller
    active_controller.on_deactivate()

    # Stop motors when switching modes
    Bridge.notify("detener")

    # Switch to new controller
    active_mode = mode
    active_controller = controllers[mode]
    active_controller.on_activate()

    # Reset auto activation when switching
    auto_active = False

    logger.info(f"Modo cambiado a: {mode}")
    web_ui.send_message("mode_changed", {"mode": mode})
    web_ui.send_message("status", {"message": f"Modo: {mode.upper()}"})

    return True


def al_recibir_distancias(d_frontal: float, d_derecho: float):
    """
    Callback for sensor data from Arduino.
    Processes data through active controller and sends commands.
    """
    global ultimo_pwm_izq, ultimo_pwm_der, auto_active, ciclos_ui

    # Throttle UI updates: Only send every 5th message (~10Hz if input is 50Hz)
    ciclos_ui += 1
    update_ui = (ciclos_ui % 5 == 0)

    # Send sensor data to UI (throttled)
    if update_ui:
        try:
            web_ui.send_message("sensores", {
                "frontal": round(d_frontal, 1),
                "derecho": round(d_derecho, 1)
            })
        except Exception as e:
            logger.warning(f"Error enviando sensores al UI: {e}")

    # Process through active controller (only for autonomous mode)
    # This remains at full speed (50Hz) for precision
    if active_mode == "auto":
        # Only compute if auto mode is active
        if not auto_active:
            return

        try:
            pwm_izq, pwm_der = active_controller.compute(d_frontal, d_derecho)
            ultimo_pwm_izq, ultimo_pwm_der = pwm_izq, pwm_der

            # Send to Arduino (using notify to avoid timeouts at 50Hz)
            Bridge.notify("motores", pwm_izq, pwm_der)

            # Update UI (throttled)
            if update_ui:
                web_ui.send_message("motores", {
                    "izquierdo": pwm_izq,
                    "derecho": pwm_der
                })
        except Exception as e:
            logger.warning(f"Error en controlador {active_mode}: {e}")


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


def on_toggle_auto(sid, data):
    """Handle auto mode activation toggle."""
    global auto_active
    auto_active = data.get("active", False)
    estado = "ACTIVADO" if auto_active else "DESACTIVADO"
    logger.info(f"Auto: {estado}")
    web_ui.send_message("auto_status", {"active": auto_active})

    if not auto_active:
        # Stop motors if deactivated
        Bridge.notify("detener")
        web_ui.send_message("motores", {"izquierdo": 0, "derecho": 0})


# --- Register callbacks ---
Bridge.provide("distancias", al_recibir_distancias)
web_ui.on_message("joystick", on_joystick_move)
web_ui.on_message("girar", on_girar)
web_ui.on_message("change_mode", on_change_mode)
web_ui.on_message("toggle_auto", on_toggle_auto)


@web_ui.on_connect
def on_connect(sid):
    """Handle new client connection."""
    logger.info(f"Cliente conectado: {sid}")

    # Send current state to new client
    web_ui.send_message("status", {"message": "Conectado al robot"})
    web_ui.send_message("mode_changed", {"mode": active_mode})


if __name__ == "__main__":
    logger.info("Iniciando Robot Joystick Control (Modular)...")
    logger.info(f"Modos disponibles: {list(controllers.keys())}")
    App.run()
