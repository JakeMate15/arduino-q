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
    x = data.get("x", 0)
    y = data.get("y", 0)
    
    # Calcular PWM para mostrar en el frontend (opcional, pero útil)
    vI = y + x
    vD = y - x
    # Limitar a -255 a 255
    vI = max(-255, min(255, vI))
    vD = max(-255, min(255, vD))
    
    try:
        # Enviar al Arduino via Bridge
        Bridge.call("joystick", x, y)
        
        # Opcional: Notificar al frontend los PWMs calculados
        web_ui.send_message("motores", {
            "izquierdo": vI,
            "derecho": vD
        })
    except Exception as e:
        logger.warning(f"Error llamando a Bridge.joystick: {e}")

# Registrar callbacks
Bridge.provide("distancias", al_recibir_distancias)
web_ui.on_message("joystick", on_joystick_move)

# Manejar conexión de clientes
@web_ui.on_connect
def on_connect(sid):
    logger.info(f"Cliente conectado: {sid}")
    # Enviar estado inicial o mensaje de bienvenida
    web_ui.send_message("status", {"message": "Conectado al robot"})

if __name__ == "__main__":
    logger.info("Iniciando aplicación Robot Joystick Control...")
    App.run()

