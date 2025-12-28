import time
import threading
from arduino.app_utils import App, Bridge, Logger

# === CONFIGURACIÓN ===
SETPOINT = 20.0       
VEL_CRUCERO = 110     # Un poco más lento ayuda a que el Twiddle aprenda mejor
CICLO_TEST = 150      
MAX_PWM = 200         # Límite de seguridad

logger = Logger("seguidor-de-pared")

def enviar_motores(vI, vD):
    logger.info(f"Motores: vI={vI} vD={vD}")
    def _call():
        try:
            Bridge.call("motores", vI, vD)
        except Exception as e:
            logger.warning(f"Error motores: {e}")
    threading.Thread(target=_call, daemon=True).start()

class AutoTuner:
    def __init__(self):
        self.p = [2.5, 12.0]  # [Kp, Kd]
        self.dp = [0.2, 1.0]  # Saltos más pequeños para mayor estabilidad
        self.mejor_error = float('inf')
        self.error_acumulado = 0
        self.muestras = 0
        self.indice = 0
        self.paso_twiddle = 0 

    def evaluar_desempeno(self):
        if self.muestras < CICLO_TEST: return
        
        error_medio = self.error_acumulado / self.muestras
        logger.info(f"EVALUANDO: Error Medio: {error_medio:.2f} | Kp: {self.p[0]:.2f} Kd: {self.p[1]:.2f}")
        
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

tuner = AutoTuner()
error_previo = 0

def clip(valor, min_v, max_v):
    return max(min(valor, max_v), min_v)

contador_mensajes = 0

def al_recibir_distancias(izq, centro, der):
    """Callback invocado por el sketch de Arduino vía Bridge.notify.
    
    Implementa control PD con auto-tuning Twiddle para seguir la pared derecha.
    
    Args:
        izq: Distancia sensor izquierdo (no usado, siempre -1)
        centro: Distancia sensor frontal en cm
        der: Distancia sensor derecho en cm
    """
    global error_previo, contador_mensajes
    
    # Debug: imprimir cada 50 mensajes (~1 segundo)
    contador_mensajes += 1
    if contador_mensajes % 50 == 1:
        logger.info(f"Recibido: centro={centro:.1f} der={der:.1f}")
    
    # --- MÁQUINA DE ESTADOS ---
    
    # 1. EMERGENCIA: Demasiado cerca de frente
    if 0 < centro < 15:
        enviar_motores(-80, 80)  # Giro sobre su eje
        error_previo = 0  # Reset para evitar pico derivativo al salir del estado
        return

    # 2. BÚSQUEDA: Si la pared derecha está muy lejos o no se ve (-1)
    if der > 45 or der <= 0:
        enviar_motores(120, 60)  # Curva suave a la derecha para buscar
        error_previo = 0
        return

    # 3. SEGUIMIENTO (PID Activo + Twiddle Activo)
    error = der - SETPOINT
    
    # Evitar saltos bruscos si acabamos de recuperar la pared
    if abs(error) > 15: 
        d_error = 0 
    else:
        d_error = error - error_previo
    
    ajuste = (tuner.p[0] * error) + (tuner.p[1] * d_error)
    error_previo = error
    
    vI = int(VEL_CRUCERO + ajuste)
    vD = int(VEL_CRUCERO - ajuste)
    
    # Aplicar límites y enviar
    enviar_motores(clip(vI, -MAX_PWM, MAX_PWM), clip(vD, -MAX_PWM, MAX_PWM))

    # --- APRENDIZAJE ---
    # Solo aprendemos si estamos en una situación de control normal
    tuner.error_acumulado += abs(error)
    tuner.muestras += 1
    
    if tuner.muestras >= CICLO_TEST:
        tuner.evaluar_desempeno()

logger.info("Registering 'distancias' callback")
Bridge.provide("distancias", al_recibir_distancias)

logger.info("Starting wall-follower robot...")
App.run()