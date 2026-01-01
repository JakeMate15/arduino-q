import sys
import time
from arduino.app_utils import App, Bridge

from controller import WallFollowerP
from runner import RunPause
from tuner import TwiddleTuner

# --- Configuración Visual y Monitoreo ---
_ciclo = 0

def label(p):
    return f"kp={p['kp']:.2f} kd={p['kd']:.2f} base={p['base']} corr={int(p['corr_max'])}"

def imprimir_cabecera():
    print("\n" + "="*95)
    # Columnas: Ciclo, Distancia, Error, Derivada, Ajuste, Motores, Visualización
    print(f"{'CICLO':<6} | {'DIST':<6} | {'ERR':<7} | {'DERIV':<7} | {'ADJ':<6} | {'PWM_I':<6} | {'PWM_D':<6} | {'GRAFICO (Setpoint |)'}")
    print("-" * 95)

def log_ciclo(info, pwm_izq, pwm_der, mode):
    global _ciclo
    _ciclo += 1
    
    if info is not None:
        dist_f, error, derivative, ajuste = info
    else:
        dist_f, error, derivative, ajuste = 0, 0, 0, 0
    
    # Representación visual rápida de la posición respecto al muro
    # El centro '|' es 15cm. 'R' es el robot.
    barra = [" "] * 15
    # Mapeamos el error a la barra (escala 1:2)
    idx_robot = int(max(0, min(14, 7 + (error * 0.5))))
    barra[7] = "|" 
    barra[idx_robot] = "R"
    visual = "".join(barra)

    print(f"{_ciclo:<6} | {dist_f:>6.1f} | {error:>7.2f} | {derivative:>7.2f} | {ajuste:>6} | {pwm_izq:>6} | {pwm_der:>6} | [{visual}] {mode}")

# --- Parámetros Iniciales ---
base_params = {
    "base": 150,
    "kp": 1.5,
    "kd": 10.0,           # Kd suele ser más alto que Kp para notar el efecto
    "corr_max": 100,
    "zona_muerta": 1.0,
    "obst_izq": -80, "obst_der": 80,
    "busc_izq": 140, "busc_der": 80,
}

tuner = TwiddleTuner(
    base_params=base_params,
    keys=("kp", "kd", "corr_max"),
    deltas=(0.5, 5.0, 20.0),
    tol=0.2, 
    reps=2,  # Cada config se prueba 2 veces para promediar
    bounds={
        "kp": (0.5, 15.0),
        "kd": (0.0, 60.0),
        "corr_max": (20.0, 150.0),
    }
)

controller = WallFollowerP(
    setpoint_derecha=15.0,
    distancia_obstaculo=15.0,
    sin_pared_umbral=300.0,
    filtro_alpha=0.7,
)

runpause = RunPause(run_seconds=6.0, pause_seconds=10.0)

# --- Lógica Principal ---
_prev_phase = None
_run_started = False

def send_motors(l, r):
    Bridge.notify("motores", int(l), int(r))

import traceback

def al_recibir_distancias(dC, dR):
    global _prev_phase, _run_started, _ciclo

    try:
        if tuner.finished:
            send_motors(0, 0)
            best_params, best_cost = tuner.best()
            print("\n" + "!"*50)
            print(f"OPTIMIZACIÓN COMPLETA")
            print(f"MEJOR CONFIG: {label(best_params)}")
            print(f"COSTO: {best_cost:.3f}")
            print("!"*50)
            sys.stdout.flush()
            return

        runpause.update()

        # --- FASE DE PAUSA ---
        if runpause.phase == "pause":
            send_motors(0, 0)

            if _prev_phase != "pause":
                if _run_started:
                    # Al terminar un RUN, mostramos resumen de desempeño
                    cost, mae, osc, sat, bad = tuner._score()
                    tuner.end_run()
                    _run_started = False

                    print("\n" + "-"*40)
                    print(f"RESUMEN RUN: Costo={cost:.3f} | MAE={mae:.2f} | OSC={osc:.2f}")
                    print(f"Próxima prueba: {label(tuner.params)}")
                    print("-"*40)

            _prev_phase = "pause"
            return

        # --- FASE DE EJECUCIÓN (RUN) ---
        if _prev_phase != "run":
            _run_started = True
            _ciclo = 0
            controller.reset()
            print(f"\n\n[INICIANDO RUN] Probando: {label(tuner.params)}")
            imprimir_cabecera()
            _prev_phase = "run"

        # 1. Calcular paso del controlador
        pwm_izq, pwm_der, mode, info = controller.step(dC, dR, tuner.params)
        
        # 2. Enviar a motores
        send_motors(pwm_izq, pwm_der)
        
        # 3. Registrar datos en el Tuner
        tuner.observe(mode, info, pwm_izq, pwm_der)
        
        # 4. Monitoreo en tiempo real (Telemetría)
        log_ciclo(info, pwm_izq, pwm_der, mode)
        
    except Exception:
        traceback.print_exc()
        sys.stdout.flush()


# --- Inicio del Programa ---
print("\nSISTEMA DE AUTO-AJUSTE PD INICIADO")
tuner.start()
runpause.start()
Bridge.provide("distancias", al_recibir_distancias)
App.run()