import sys
from arduino.app_utils import App, Bridge

from controller import WallFollowerP
from runner import RunPause
from tuner import TwiddleTuner

print("\n\n\n\n\n\n\n\n")
print("==================================================")
print("--- Auto ajuste (TWIDDLE) | RUN 10s / PAUSA 10s ---")
sys.stdout.flush()

def label(p):
    return f"kp={p['kp']:.2f} kd={p['kd']:.2f} base={p['base']} corr={int(p['corr_max'])}"

base_params = {
    "base": 100,
    "kp": 2.0,
    "kd": 1.0,           # NUEVO: Valor inicial sugerido para Kd
    "corr_max": 80,
    "zona_muerta": 1.0,
    "obst_izq": -80, "obst_der": 80,
    "busc_izq": 140, "busc_der": 80,
}

tuner = TwiddleTuner(
    base_params=base_params,
    keys=("kp", "kd", "corr_max"),
    
    # Deltas iniciales (cuánto salta el valor al probar):
    # kp salta 0.5, kd salta 1.0, corr_max salta 10
    deltas=(1.0, 2.0, 20.0),
    
    tol=0.2, # Tolerancia para detenerse (suma de deltas)
    reps=2,  # Repeticiones por configuración
    
    bounds={
        "kp": (0.5, 15.0),
        "kd": (0.0, 50.0),      # NUEVO: Limites para Kd (no negativo, max razonable)
        "corr_max": (20.0, 150.0),
    }
)
tuner.start()

controller = WallFollowerP(
    setpoint_derecha=15.0,
    distancia_obstaculo=15.0,
    sin_pared_umbral=300.0,
    filtro_alpha=0.7,
)

runpause = RunPause(run_seconds=10.0, pause_seconds=15.0)
runpause.start()

_prev_phase = runpause.phase
_run_started = False

def send_motors(l, r):
    Bridge.notify("motores", int(l), int(r))

def al_recibir_distancias(dC, dR):
    global _prev_phase, _run_started

    if tuner.finished:
        send_motors(0, 0)
        best_params, best_cost = tuner.best()
        print("\n=== TERMINADO ===")
        print(f"MEJOR: {label(best_params)} | best_cost={best_cost:.3f}")
        sys.stdout.flush()
        return

    runpause.update()

    if runpause.phase == "pause":
        send_motors(0, 0)

        if _prev_phase != "pause":
            if _run_started:
                action = tuner.end_run()
                _run_started = False

                if tuner.finished:
                    return

                controller.reset()
                print(f"\n[PAUSA {runpause.pause_s:.0f}s] siguiente: {label(tuner.params)}  (sum_deltas={sum(tuner.deltas):.3f})")
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
