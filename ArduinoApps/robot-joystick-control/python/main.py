import csv
import os
from datetime import datetime
from arduino.app_utils import App, Bridge, Logger
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_objectdetection import VideoObjectDetection

logger = Logger("robot-joystick-control")
web_ui = WebUI()
# Iniciar el motor de video (proporciona el stream en puerto 4912)
# No registraremos callbacks de detección para que solo sea video
camera_stream = VideoObjectDetection()

# --- Configuración de Grabación ---
# El archivo se guarda en el directorio de la aplicación Python
DIR_DATOS = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_DATOS = os.path.join(DIR_DATOS, "recorrido_robot.csv")
grabando = False
ultimo_pwm_izq = 0
ultimo_pwm_der = 0

# Inicializar CSV si no existe
if not os.path.exists(ARCHIVO_DATOS):
    try:
        with open(ARCHIVO_DATOS, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'dist_frontal', 'dist_derecho', 'pwm_izq', 'pwm_der'])
        logger.info(f"Archivo de datos creado: {ARCHIVO_DATOS}")
    except Exception as e:
        logger.warning(f"No se pudo crear el archivo CSV: {e}")
else:
    logger.info(f"Archivo de datos existente encontrado: {ARCHIVO_DATOS}")

# Callback para recibir distancias desde el Arduino
def al_recibir_distancias(d_frontal, d_derecho):
    """Recibe distancias del Arduino y las envía al frontend."""
    global grabando, ultimo_pwm_izq, ultimo_pwm_der
    
    # Enviar al UI siempre para visualización
    try:
        web_ui.send_message("sensores", {
            "frontal": round(d_frontal, 1),
            "derecho": round(d_derecho, 1)
        })
    except Exception as e:
        logger.warning(f"Error enviando distancias al UI: {e}")

    # Lógica de Grabación (Caja Negra)
    if grabando:
        # Solo grabar si hay movimiento significativo (evita datos estáticos irrelevantes)
        if abs(ultimo_pwm_izq) > 5 or abs(ultimo_pwm_der) > 5:
            try:
                with open(ARCHIVO_DATOS, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        datetime.now().isoformat(),
                        round(d_frontal, 2),
                        round(d_derecho, 2),
                        ultimo_pwm_izq,
                        ultimo_pwm_der
                    ])
            except Exception as e:
                logger.warning(f"Error escribiendo en CSV: {e}")

# Manejador de mensajes del WebSocket (Joystick)
def on_joystick_move(sid, data):
    """Recibe movimiento del joystick desde el frontend y lo envía al Arduino."""
    global ultimo_pwm_izq, ultimo_pwm_der
    
    x = data.get("x", 0)
    y = data.get("y", 0)
    
    # Límite de PWM configurado en Arduino
    MAX_PWM_LIMIT = 255
    
    # Escalar los valores del joystick (-255 a 255) al rango limitado
    def scale(val):
        return int((val / 255.0) * (MAX_PWM_LIMIT / 2.0))

    scaledX = scale(x)
    scaledY = scale(y)
    
    # Calcular PWM para mostrar en el frontend y para grabar
    vI = scaledY + scaledX
    vD = scaledY - scaledX
    
    # Limitar por seguridad
    ultimo_pwm_izq = max(-MAX_PWM_LIMIT, min(MAX_PWM_LIMIT, vI))
    ultimo_pwm_der = max(-MAX_PWM_LIMIT, min(MAX_PWM_LIMIT, vD))
    
    try:
        # Enviar al Arduino via Bridge
        Bridge.call("joystick", x, y)
        
        # Notificar al frontend los PWMs
        web_ui.send_message("motores", {
            "izquierdo": ultimo_pwm_izq,
            "derecho": ultimo_pwm_der
        })
    except Exception as e:
        logger.warning(f"Error llamando a Bridge.joystick: {e}")

def on_girar(sid, data):
    global ultimo_pwm_izq, ultimo_pwm_der
    direccion = data.get("dir")
    accion = data.get("action") # "start" o "stop"
    
    # Límite específico para giro con botones
    VEL_GIRO = 150
    
    try:
        if accion == "stop":
            Bridge.call("detener")
            ultimo_pwm_izq, ultimo_pwm_der = 0, 0
        elif direccion == "izq":
            Bridge.call("girar_izq")
            ultimo_pwm_izq, ultimo_pwm_der = -VEL_GIRO, VEL_GIRO
        elif direccion == "der":
            Bridge.call("girar_der")
            ultimo_pwm_izq, ultimo_pwm_der = VEL_GIRO, -VEL_GIRO
        
        web_ui.send_message("motores", {"izquierdo": ultimo_pwm_izq, "derecho": ultimo_pwm_der})
    except Exception as e:
        logger.warning(f"Error en comando de giro: {e}")

def on_toggle_recording(sid, data):
    """Maneja el inicio/fin de la grabación de datos."""
    global grabando
    grabando = data.get("active", False)
    estado = "INICIADA" if grabando else "DETENIDA"
    logger.info(f"Grabación de datos: {estado} -> Archivo: {ARCHIVO_DATOS}")
    web_ui.send_message("status", {"message": f"Grabación {estado}"})

# Registrar callbacks
Bridge.provide("distancias", al_recibir_distancias)
web_ui.on_message("joystick", on_joystick_move)
web_ui.on_message("girar", on_girar)
web_ui.on_message("toggle_recording", on_toggle_recording)

# Manejar conexión de clientes
@web_ui.on_connect
def on_connect(sid):
    logger.info(f"Cliente conectado: {sid}")
    web_ui.send_message("status", {"message": "Conectado al robot"})

if __name__ == "__main__":
    logger.info("Iniciando aplicación Robot Joystick Control (Modo Recolección IA)...")
    App.run()
