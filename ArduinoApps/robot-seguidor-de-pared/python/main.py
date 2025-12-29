import time
from arduino.app_utils import App, Bridge, Logger

logger = Logger("seguidor-pared")

SETPOINT_DERECHA = 15.0
KP = 1.5
VELOCIDAD_BASE = 100
DISTANCIA_OBSTACULO = 15.0

CORR_MAX = 40
SIN_PARED_UMBRAL = 300.0
ZONA_MUERTA = 1.0

dR_f = None

def clip(x, lo, hi):
    return max(lo, min(hi, x))

def al_recibir_distancias(dC, dR):
    global dR_f

    if dC <= DISTANCIA_OBSTACULO:
        Bridge.notify("motores", -80, 80)
        return

    if dR >= SIN_PARED_UMBRAL:
        Bridge.notify("motores", 140, 80)
        return

    if dR_f is None:
        dR_f = dR
    dR_f = 0.7 * dR_f + 0.3 * dR

    error = dR_f - SETPOINT_DERECHA

    if abs(error) <= ZONA_MUERTA:
        ajuste = 0
    else:
        ajuste = clip(int(KP * error), -CORR_MAX, CORR_MAX)

    pwm_izq = int(clip(VELOCIDAD_BASE + ajuste, 0, 255))
    pwm_der = int(clip(VELOCIDAD_BASE - ajuste, 0, 255))

    Bridge.notify("motores", pwm_izq, pwm_der)
    logger.info(f"dC={dC:.1f} dR={dR:.1f} fR={dR_f:.1f} e={error:.1f} a={ajuste} m={pwm_izq}/{pwm_der}")

Bridge.provide("distancias", al_recibir_distancias)

def loop():
    time.sleep(1)

if __name__ == "__main__":
    App.run(user_loop=loop)
