import time
import sys
from arduino.app_utils import App, Bridge

from controller import WallFollowerP
from runner import RunPause

print("--- Robot Seguidor de Pared (Control P + Run/Pause) ---")
sys.stdout.flush()

controller = WallFollowerP(
    setpoint_derecha=15.0,
    kp=1.5,
    velocidad_base=100,
    distancia_obstaculo=15.0,
    corr_max=40,
    sin_pared_umbral=300.0,
    zona_muerta=1.0,
    filtro_alpha=0.7,
)

runpause = RunPause(run_seconds=3.0, pause_seconds=10.0)
runpause.start()

_prev_phase = runpause.phase

def al_recibir_distancias(dC, dR):
    global _prev_phase

    change = runpause.update()
    if change == "to_pause":
        Bridge.notify("motores", 0, 0)
    elif change == "to_run":
        pass

    if runpause.phase == "pause":
        Bridge.notify("motores", 0, 0)
        if _prev_phase != "pause":
            print(f"[PAUSA] {runpause.pause_s:.1f}s para regresar al inicio")
            sys.stdout.flush()
        _prev_phase = "pause"
        return

    pwm_izq, pwm_der, info = controller.step(dC, dR)
    Bridge.notify("motores", pwm_izq, pwm_der)

    if info == "obst":
        print(f">> C:{dC:5.1f} R:{dR:5.1f}  [OBST]  m:{pwm_izq}/{pwm_der}  run:{runpause.time_left:4.1f}s")
    elif info == "buscar":
        print(f">> C:{dC:5.1f} R:{dR:5.1f} [BUSCAR] m:{pwm_izq}/{pwm_der}  run:{runpause.time_left:4.1f}s")
    else:
        dR_f, error, ajuste = info
        print(f">> C:{dC:5.1f} R:{dR:5.1f} F:{dR_f:5.1f} E:{error:5.1f} A:{ajuste:4d} m:{pwm_izq}/{pwm_der} run:{runpause.time_left:4.1f}s")
    sys.stdout.flush()

    if _prev_phase != "run":
        print(f"[RUN] {runpause.run_s:.1f}s")
        sys.stdout.flush()
    _prev_phase = "run"

Bridge.provide("distancias", al_recibir_distancias)


App.run()