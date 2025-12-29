import time
from arduino.app_utils import App, Bridge, Logger

logger = Logger("seguidor-pared")

SETPOINT_DERECHA = 15.0
KP = 3.5
VELOCIDAD_BASE = 120
DISTANCIA_OBSTACULO = 15.0

CORR_MAX = 70
SIN_PARED_UMBRAL = 300.0

def clip(x, lo, hi):
    return max(lo, min(hi, x))

def al_recibir_distancias(dist_centro, dist_derecha):
    if dist_centro <= DISTANCIA_OBSTACULO:
        Bridge.notify("motores", -80, 80)
        return

    if dist_derecha >= SIN_PARED_UMBRAL:
        Bridge.notify("motores", 140, 80)
        return

    error = SETPOINT_DERECHA - dist_derecha  # invierte el signo si gira al lado incorrecto
    ajuste = clip(int(KP * error), -CORR_MAX, CORR_MAX)

    pwm_izq = int(clip(VELOCIDAD_BASE + ajuste, 0, 255))
    pwm_der = int(clip(VELOCIDAD_BASE - ajuste, 0, 255))

    Bridge.notify("motores", pwm_izq, pwm_der)
    logger.info(f"dC={dist_centro:.1f} dR={dist_derecha:.1f} err={error:.1f} adj={ajuste} m={pwm_izq}/{pwm_der}")

Bridge.provide("distancias", al_recibir_distancias)

def loop():
    time.sleep(1)

if __name__ == "__main__":
    App.run(user_loop=loop)
