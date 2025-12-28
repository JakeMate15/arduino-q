import time
import threading
from arduino.app_utils import App, Bridge, Logger

# === CONFIGURACIÓN ===
SETPOINT = 20.0       # Distancia ideal a la pared derecha (cm)
VEL_CRUCERO = 110     # Velocidad base
MAX_PWM = 200         # Límite de potencia
CICLO_TEST = 150      # Muestras para el auto-tuning Twiddle

# Estados
ESTADO_NORMAL = "NORMAL"
ESTADO_GIRANDO_IZQ = "GIRANDO_IZQ"
ESTADO_GIRANDO_DER = "GIRANDO_DER"

logger = Logger("seguidor-de-pared")

# === UTILIDADES ===
def clip(valor, min_v, max_v):
    return max(min(valor, max_v), min_v)

def enviar_motores(vI, vD):
    """Envía comandos de velocidad al Arduino en un hilo separado para no bloquear."""
    def _call():
        try:
            Bridge.call("motores", vI, vD)
        except Exception as e:
            logger.warning(f"Error comunicación motores: {e}")
    threading.Thread(target=_call, daemon=True).start()

# === CLASE DE AUTO-CALIBRACIÓN (TWIDDLE) ===
class AutoTuner:
    def __init__(self):
        self.p = [2.5, 12.0]  # [Kp, Kd] iniciales
        self.dp = [0.2, 1.0]  # Saltos de búsqueda
        self.mejor_error = float('inf')
        self.error_acumulado = 0
        self.muestras = 0
        self.indice = 0
        self.paso_twiddle = 0 

    def evaluar_desempeno(self):
        if self.muestras < CICLO_TEST: return
        
        error_medio = self.error_acumulado / self.muestras
        logger.info(f"--- TEST TWIDDLE --- Error: {error_medio:.2f} | Kp: {self.p[0]:.2f} Kd: {self.p[1]:.2f}")
        
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

# === LÓGICA PRINCIPAL ===
tuner = AutoTuner()
error_previo = 0
estado_actual = ESTADO_NORMAL
contador_mensajes = 0



def al_recibir_distancias(izq, centro, der):
    global error_previo, estado_actual, contador_mensajes
    
    contador_mensajes += 1
    if contador_mensajes % 50 == 1:
        logger.info(f"Sensores -> C: {centro:.1f} D: {der:.1f} | Modo: {estado_actual}")
    
    # --- 1. GESTIÓN DE ESTADOS DE BLOQUEO (GIROS) ---

    if estado_actual == ESTADO_GIRANDO_IZQ:
        # Salida: Frente despejado Y volvemos a ver la pared derecha
        if centro > 35 and (0 < der < 35):
            estado_actual = ESTADO_NORMAL
            logger.info(">>> Vuelta Izquierda COMPLETADA")
        else:
            enviar_motores(-100, 100) # Rotación pura a la izquierda
            return

    elif estado_actual == ESTADO_GIRANDO_DER:
        # Salida: Recuperamos contacto con la pared derecha
        if 0 < der < 30:
            estado_actual = ESTADO_NORMAL
            logger.info(">>> Vuelta Derecha COMPLETADA")
        else:
            enviar_motores(110, -30) # Pivotar agresivo a la derecha
            return

    # --- 2. DETECCIÓN DE TRANSICIONES ---

    # Prioridad 1: Obstáculo frontal (Esquina interna)
    if 0 < centro < 18:
        estado_actual = ESTADO_GIRANDO_IZQ
        enviar_motores(-100, 100)
        error_previo = 0
        return

    # Prioridad 2: Pérdida de pared derecha (Esquina externa / final de muro)
    if der > 45 or der <= 0:
        estado_actual = ESTADO_GIRANDO_DER
        enviar_motores(110, -30)
        error_previo = 0
        return

    # --- 3. MODO NORMAL: SEGUIMIENTO PID + APRENDIZAJE ---

    error = der - SETPOINT
    
    # Cálculo derivativo (amortiguador)
    d_error = error - error_previo
    ajuste = (tuner.p[0] * error) + (tuner.p[1] * d_error)
    error_previo = error
    
    vI = int(VEL_CRUCERO + ajuste)
    vD = int(VEL_CRUCERO - ajuste)
    
    enviar_motores(clip(vI, -MAX_PWM, MAX_PWM), clip(vD, -MAX_PWM, MAX_PWM))

    # El Twiddle solo aprende en rectas (estado NORMAL)
    tuner.error_acumulado += abs(error)
    tuner.muestras += 1
    if tuner.muestras >= CICLO_TEST:
        tuner.evaluar_desempeno()

# Configuración de Bridge y arranque
Bridge.provide("distancias", al_recibir_distancias)
logger.info("Robot iniciado. Esperando telemetría...")
App.run()