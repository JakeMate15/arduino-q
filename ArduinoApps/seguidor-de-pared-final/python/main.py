import sys
from arduino.app_utils import App, Bridge

from controller import WallFollowerP
from runner import RunPause
from tuner import SweepTuner

print("\n\n\n\n\n\n\n\n")
print("==================================================")
print("--- Auto ajuste (barrido) | RUN 5s / PAUSA 10s ---")
sys.stdout.flush()

def label(p):
    return f"kp={p['kp']:.2f} base={p['base']} corr={p['corr_max']} zona={p['zona_muerta']:.1f}"

def make_candidates():
    base = 100
    corr_max = 40
    zona = 1.0
    kp_list = [0.6, 0.9, 1.2, 1.5, 1.8, 2.2, 2.6, 3.0]

    out = []
    for kp in kp_list:
        out.append({
            "base": base,
            "kp": kp,
            "corr_max": corr_max,
            "zona_muerta": zona,
            "obst_izq": -80, "obst_der": 80,
            "busc_izq": 140, "busc_der": 80,
        })
    return out

controller = WallFollowerP(
    setpoint_derecha=15.0,
    distancia_obstaculo=15.0,
    sin_pared_umbral=300.0,
    filtro_alpha=0.7,
)

tuner = SweepTuner(make_candidates())
tuner.start()

runpause = RunPause(run_seconds=6.5, pause_seconds=10.0)
runpause.start()

_prev_phase = runpause.phase
_run_started = False

def send_motors(l, r):
    Bridge.notify("motores", int(l), int(r))

def al_recibir_distancias(dC, dR):
    global _prev_phase, _run_started

    if tuner.finished:
        send_motors(0, 0)
        best = tuner.best()
        print("\n=== RESULTADOS ===")
        for params, cost, mae, osc, sat, bad in tuner.results:
            print(f"{label(params)} | cost={cost:7.3f} mae={mae:6.3f} osc={osc:6.3f} sat={sat:6.2%} bad={bad}")
        if best:
            bparams, cost, mae, osc, sat, bad = best
            print(f"\n=== MEJOR === {label(bparams)} | cost={cost:.3f}")
        sys.stdout.flush()
        return

    change = runpause.update()

    if runpause.phase == "pause":
        send_motors(0, 0)

        if _prev_phase != "pause":
            if _run_started:
                tuner.end_run()
                _run_started = False

            if tuner.finished:
                return

            controller.reset()
            print(f"\n[PAUSA {runpause.pause_s:.0f}s] siguiente: {label(tuner.params)}")
            sys.stdout.flush()

        _prev_phase = "pause"
        return

    if _prev_phase != "run":
        _run_started = True
        print(f"\n[RUN {runpause.run_s:.0f}s] probando {label(tuner.params)}")
        sys.stdout.flush()
        _prev_phase = "run"

    pwm_izq, pwm_der, mode, info = controller.step(dC, dR, tuner.params)
    send_motors(pwm_izq, pwm_der)
    tuner.observe(mode, info, pwm_izq, pwm_der)

Bridge.provide("distancias", al_recibir_distancias)

App.run()
