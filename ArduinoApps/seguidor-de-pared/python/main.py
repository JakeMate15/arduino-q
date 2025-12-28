import time
from arduino.app_utils import App, Bridge

# === CONFIGURACIÓN INICIAL ===
SETPOINT = 20.0       # Distancia ideal a la pared (cm)
VEL_CRUCERO = 120     # Velocidad base de los motores
CICLO_TEST = 150      # Cantidad de lecturas para evaluar un parámetro

class AutoTuner:
    def __init__(self):
        # Parámetros [Kp, Kd]
        self.p = [2.5, 12.0]  
        self.dp = [0.5, 2.0]  
        self.mejor_error = float('inf')
        self.error_acumulado = 0
        self.muestras = 0
        self.indice = 0
        self.paso_twiddle = 0 # 0: Probando aumento, 1: Probando disminución

    def evaluar_desempeno(self):
        error_medio = self.error_acumulado / self.muestras
        print(f"\n>> TEST FINALIZADO. Error Medio: {error_medio:.2f}")
        
        i = self.indice
        if self.paso_twiddle == 0:
            if error_medio < self.mejor_error:
                self.mejor_error = error_medio
                self.dp[i] *= 1.1
                self.indice = (self.indice + 1) % 2
                self.p[self.indice] += self.dp[self.indice]
            else:
                self.p[i] -= 2 * self.dp[i]
                self.paso_twiddle = 1
        else:
            if error_medio < self.mejor_error:
                self.mejor_error = error_medio
                self.dp[i] *= 1.1
            else:
                self.p[i] += self.dp[i]
                self.dp[i] *= 0.9
            
            self.indice = (self.indice + 1) % 2
            self.p[self.indice] += self.dp[self.indice]
            self.paso_twiddle = 0

        self.error_acumulado = 0
        self.muestras = 0
        print(f">> NUEVOS VALORES: Kp={self.p[0]:.2f}, Kd={self.p[1]:.2f}\n")

tuner = AutoTuner()
error_previo = 0

def al_recibir_distancias(izq, centro, der):
    global error_previo
    
    # --- MÁQUINA DE ESTADOS ---
    # 1. EMERGENCIA: Pared al frente
    if 0 < centro < 15:
        Bridge.call("motores", -100, 100)
        return

    # 2. BÚSQUEDA: Pared derecha se perdió
    if der > 50 or der < 0:
        Bridge.call("motores", 130, 70) # Giro suave a la derecha
        return

    # 3. SEGUIMIENTO (PID + TWIDDLE)
    error = der - SETPOINT
    d_error = error - error_previo
    
    ajuste = (tuner.p[0] * error) + (tuner.p[1] * d_error)
    error_previo = error
    
    # Enviar a motores
    vI = int(VEL_CRUCERO + ajuste)
    vD = int(VEL_CRUCERO - ajuste)
    Bridge.call("motores", vI, vD)

    # Acumular para Twiddle
    tuner.error_acumulado += abs(error)
    tuner.muestras += 1

    if tuner.muestras >= CICLO_TEST:
        tuner.evaluar_desempeno()

Bridge.provide("distancias", al_recibir_distancias)
App.run()