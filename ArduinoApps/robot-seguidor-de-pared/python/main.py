import time
from arduino.app_utils import App, Bridge, Logger

logger = Logger("seguidor-pared")

def al_recibir_distancias(dist_centro, dist_derecha):
    """Callback que se ejecuta cuando el Arduino envía distancias."""
    logger.info(f"Sensores -> Centro: {dist_centro:.1f} cm | Derecha: {dist_derecha:.1f} cm")

# Registramos la función para recibir la notificación "distancias" desde el Arduino
Bridge.provide("distancias", al_recibir_distancias)

def loop():
    """Esta función se ejecuta repetidamente."""
    time.sleep(1)

if __name__ == "__main__":
    logger.info("Iniciando App Seguidor de Pared...")
    App.run(user_loop=loop)
