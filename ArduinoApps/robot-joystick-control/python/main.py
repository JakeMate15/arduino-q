from arduino.app_utils import App, Bridge, Logger
from arduino.app_bricks.web_ui import WebUI

logger = Logger("robot-joystick-control")
web_ui = WebUI()

# Callback para recibir distancias desde el Arduino
def al_recibir_distancias(d_frontal, d_derecho):
    """Recibe distancias del Arduino y las envía al frontend."""
    # logger.debug(f"Sensores -> Frontal: {d_frontal:.1f} cm, Derecho: {d_derecho:.1f} cm")
    try:
        web_ui.send_message("sensores", {
            "frontal": round(d_frontal, 1),
            "derecho": round(d_derecho, 1)
        })
    except Exception as e:
        logger.warning(f"Error enviando distancias al UI: {e}")

# Manejador de mensajes del WebSocket (Joystick)
def on_joystick_move(sid, data):
    """Recibe movimiento del joystick desde el frontend y lo envía al Arduino."""
    y = data.get("y", 0)
    
    # Límite de PWM configurado en Arduino
    MAX_PWM_LIMIT = 150
    
    # Escalar solo el eje Y (-255 a 255) al rango limitado (-150 a 150)
    v_base = int((y / 255.0) * MAX_PWM_LIMIT)
    
    try:
        # Enviar al Arduino via Bridge (enviamos el original y el Arduino lo escala)
        # Enviamos x=0 porque ahora el giro es por botones
        Bridge.call("joystick", 0, y)
        
        # Notificar al frontend los PWMs
        web_ui.send_message("motores", {
            "izquierdo": v_base,
            "derecho": v_base
        })
    except Exception as e:
        logger.warning(f"Error llamando a Bridge.joystick: {e}")

def on_girar(sid, data):
    direccion = data.get("dir")
    accion = data.get("action") # "start" o "stop"
    
    try:
        if accion == "stop":
            Bridge.call("detener")
            web_ui.send_message("motores", {"izquierdo": 0, "derecho": 0})
        elif direccion == "izq":
            Bridge.call("girar_izq")
            web_ui.send_message("motores", {"izquierdo": -150, "derecho": 150})
        elif direccion == "der":
            Bridge.call("girar_der")
            web_ui.send_message("motores", {"izquierdo": 150, "derecho": -150})
    except Exception as e:
        logger.warning(f"Error en comando de giro: {e}")

# Registrar callbacks
Bridge.provide("distancias", al_recibir_distancias)
web_ui.on_message("joystick", on_joystick_move)
web_ui.on_message("girar", on_girar)

# Manejar conexión de clientes
@web_ui.on_connect
def on_connect(sid):
    logger.info(f"Cliente conectado: {sid}")
    # Enviar estado inicial o mensaje de bienvenida
    web_ui.send_message("status", {"message": "Conectado al robot"})

if __name__ == "__main__":
    logger.info("Iniciando aplicación Robot Joystick Control...")
    App.run()

