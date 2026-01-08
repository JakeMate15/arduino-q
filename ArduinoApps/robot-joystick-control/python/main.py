"""
Control de Robot con Joystick - Aplicación Principal
Orquesta controladores (Manual, Automático) y maneja comunicación WebSocket
"""
from datetime import datetime, UTC
from arduino.app_utils import App, Bridge, Logger
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_objectdetection import VideoObjectDetection

from controllers import ManualController, AutoController

logger = Logger("robot-joystick-control")
web_ui = WebUI()

# Detección de objetos con cámara
detection_stream = VideoObjectDetection(confidence=0.5, debounce_sec=0.0)
camera_enabled = True

# Controladores disponibles
controllers = {
    "manual": ManualController(),
    "auto": AutoController()
}

active_mode = "manual"
active_controller = controllers["manual"]

# Estado
ultimo_pwm_izq = 0
ultimo_pwm_der = 0
auto_active = False
ciclos_ui = 0  # Contador para limitar actualizaciones de UI
all_detected_objects = {}

logger.info("Controladores disponibles: manual, auto")


def on_detect_objects(detections: dict):
    """Callback cuando la cámara detecta objetos"""
    global all_detected_objects
    all_detected_objects = detections

    controllers["auto"].update_detections(detections)

    # Enviar cada detección a la interfaz web
    for obj_name, obj_data in detections.items():
        entry = {
            "content": obj_name,
            "confidence": obj_data.get("confidence"),
            "timestamp": datetime.now(UTC).isoformat()
        }
        web_ui.send_message("detection", message=entry)


detection_stream.on_detect_all(on_detect_objects)


def set_mode(mode: str) -> bool:
    """Cambia el modo de control del robot"""
    global active_mode, active_controller, auto_active

    if mode not in controllers:
        logger.warning(f"Modo desconocido: {mode}")
        return False

    active_controller.on_deactivate()
    Bridge.notify("detener")

    active_mode = mode
    active_controller = controllers[mode]
    active_controller.on_activate()
    auto_active = False

    logger.info(f"Modo cambiado a: {mode}")
    web_ui.send_message("mode_changed", {"mode": mode})
    return True


def al_recibir_distancias(d_frontal: float, d_derecho: float):
    """Callback de sensores del Arduino - Procesa datos y envía comandos"""
    global ultimo_pwm_izq, ultimo_pwm_der, auto_active, ciclos_ui

    ciclos_ui += 1
    update_ui = (ciclos_ui % 5 == 0)  # Actualizar UI cada 5 ciclos (~10Hz)

    if update_ui:
        try:
            web_ui.send_message("sensores", {
                "frontal": round(d_frontal, 1),
                "derecho": round(d_derecho, 1)
            })
        except Exception as e:
            logger.warning(f"Error enviando sensores: {e}")

    if active_mode == "auto" and auto_active:
        try:
            pwm_izq, pwm_der = active_controller.compute(d_frontal, d_derecho)
            ultimo_pwm_izq, ultimo_pwm_der = pwm_izq, pwm_der

            Bridge.notify("motores", pwm_izq, pwm_der)

            if update_ui:
                web_ui.send_message("motores", {
                    "izquierdo": pwm_izq,
                    "derecho": pwm_der
                })
        except Exception as e:
            logger.warning(f"Error en controlador auto: {e}")


def on_joystick_move(sid, data):
    """Maneja entrada del joystick desde la interfaz web"""
    global ultimo_pwm_izq, ultimo_pwm_der

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
    """Maneja botones de giro desde la interfaz web"""
    global ultimo_pwm_izq, ultimo_pwm_der

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
    """Maneja cambio de modo desde la interfaz web"""
    mode = data.get("mode", "manual")
    set_mode(mode)


def on_toggle_auto(sid, data):
    """Activa/desactiva el controlador automático"""
    global auto_active
    auto_active = data.get("active", False)
    estado = "ACTIVADO" if auto_active else "DESACTIVADO"
    logger.info(f"Control automático: {estado}")

    if not auto_active:
        Bridge.notify("detener")
        web_ui.send_message("motores", {"izquierdo": 0, "derecho": 0})


def on_set_object_lists(sid, data):
    """Actualiza listas de objetos para el controlador automático"""
    list_a = data.get("list_a", [])
    list_b = data.get("list_b", [])
    controllers["auto"].set_object_lists(list_a, list_b)
    logger.info(f"Listas actualizadas - A: {list_a}, B: {list_b}")


def on_override_confidence(sid, threshold):
    """Actualiza umbral de confianza para detección de objetos"""
    detection_stream.override_threshold(threshold)
    logger.info(f"Umbral de confianza: {threshold}")


def on_toggle_camera(sid, data):
    """Muestra/oculta el video (la detección sigue activa)"""
    global camera_enabled
    camera_enabled = data.get("enabled", True)

    # Solo enviamos el estado a la UI para ocultar/mostrar el video
    # La detección de objetos sigue funcionando en segundo plano
    estado = "visible" if camera_enabled else "oculto"
    logger.info(f"Video stream: {estado}")

    web_ui.send_message("camera_status", {"enabled": camera_enabled})


def on_console_message(sid, data):
    """Imprime mensaje desde la interfaz web en la consola"""
    message = data.get("message", "")
    logger.info(f"[UI] {message}")
    print(f"\n>>> Mensaje desde UI: {message}\n")


# Registrar callbacks
Bridge.provide("distancias", al_recibir_distancias)
web_ui.on_message("joystick", on_joystick_move)
web_ui.on_message("girar", on_girar)
web_ui.on_message("change_mode", on_change_mode)
web_ui.on_message("toggle_auto", on_toggle_auto)
web_ui.on_message("set_object_lists", on_set_object_lists)
web_ui.on_message("override_th", on_override_confidence)
web_ui.on_message("toggle_camera", on_toggle_camera)
web_ui.on_message("console_message", on_console_message)


@web_ui.on_connect
def on_connect(sid):
    """Maneja nueva conexión de cliente"""
    logger.info(f"Cliente conectado: {sid}")
    web_ui.send_message("status", {"message": "Conectado al robot"})
    web_ui.send_message("mode_changed", {"mode": active_mode})
    web_ui.send_message("object_lists", controllers["auto"].get_object_lists())
    web_ui.send_message("camera_status", {"enabled": camera_enabled})


if __name__ == "__main__":
    logger.info("Iniciando Control de Robot...")
    logger.info(f"Modos: {list(controllers.keys())}")
    App.run()
