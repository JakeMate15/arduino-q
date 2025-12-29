import time
from arduino.app_utils import App, Bridge, Logger

logger = Logger("seguidor-pared")

# --- Configuración del Controlador Proporcional ---
SETPOINT_DERECHA = 15.0  # Distancia deseada a la pared derecha (cm)
KP = 3.5                # Ganancia proporcional
VELOCIDAD_BASE = 120    # Velocidad de crucero
DISTANCIA_OBSTACULO = 15.0 # Distancia para frenar si hay algo en frente

def al_recibir_distancias(dist_centro, dist_derecha):
    """
    Controlador Proporcional ejecutado en Python.
    Recibe sensores y envía comandos de motor.
    """
    # 1. Seguridad: Si hay un obstáculo en frente, nos detenemos o giramos
    if dist_centro < DISTANCIA_OBSTACULO and dist_centro > 0:
        logger.warning(f"¡Obstáculo detectado! Centro: {dist_centro:.1f} cm")
        # Giramos a la izquierda para alejarnos de la pared/obstáculo
        Bridge.notify("motores", -80, 80)
        return

    # 2. Lógica del Seguidor de Pared (Control Proporcional)
    # Error = Distancia deseada - Distancia actual
    error = SETPOINT_DERECHA - dist_derecha
    
    # Ajuste = KP * Error
    ajuste = int(KP * error)
    
    # Calculamos velocidades para cada motor
    # Si estamos muy cerca (dist_derecha < 15), el error es positivo -> ajuste positivo
    # Motor Izquierdo aumenta, Motor Derecho disminuye -> gira a la izquierda (se aleja de la pared)
    pwm_izquierdo = VELOCIDAD_BASE + ajuste
    pwm_derecho = VELOCIDAD_BASE - ajuste
    
    # 3. Enviamos los comandos al Arduino
    Bridge.notify("motores", pwm_izquierdo, pwm_derecho)
    
    logger.info(f"Dist: {dist_derecha:.1f} | Error: {error:.1f} | Motores: {pwm_izquierdo}/{pwm_derecho}")

# Registramos el callback para recibir datos del Arduino
Bridge.provide("distancias", al_recibir_distancias)

def loop():
    """Mantenemos la app viva."""
    time.sleep(1)

if __name__ == "__main__":
    logger.info("Iniciando Controlador Proporcional en Python...")
    App.run(user_loop=loop)
