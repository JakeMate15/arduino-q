# Explicación del Controlador PID

Este documento explica cómo funciona el controlador PID implementado en este proyecto para que el robot pueda seguir una pared derecha a una distancia constante.

## ¿Qué es un PID?

PID significa **Proporcional, Integral y Derivativo**. Es un mecanismo de control por realimentación que calcula un "error" (la diferencia entre lo que queremos y lo que tenemos) y aplica una corrección basada en tres términos.

En nuestro caso:
- **Variable de Proceso (PV):** Distancia actual medida por el sensor derecho.
- **Setpoint (SP):** Distancia ideal a la que queremos estar de la pared (ej. 15 cm).
- **Error (e):** `Distancia Actual - Setpoint`.

---

## Los Tres Componentes

### 1. Proporcional (P) - "El Presente"
Es la corrección más simple. Multiplica el error actual por una ganancia $K_p$.
- **Fórmula:** $P = K_p \times \text{error}$
- **Efecto:** Si el robot está muy lejos de la pared, aplica mucha fuerza para acercarse. Si está cerca, aplica poca.
- **Problema:** Si solo usamos P, el robot nunca llegará exactamente al setpoint o empezará a oscilar de un lado a otro.

### 2. Integral (I) - "El Pasado"
Acumula los errores pasados a lo largo del tiempo.
- **Fórmula:** $I = K_i \times \sum (\text{error} \times \Delta t)$
- **Efecto:** Si el robot lleva mucho tiempo con un pequeño error que el término P no logra corregir (por ejemplo, por fricción o motores desiguales), el término I irá creciendo hasta que el robot se mueva.
- **Seguridad:** En el código usamos un "Anti-windup" para evitar que este valor crezca infinitamente.

### 3. Derivativo (D) - "El Futuro"
Predice la tendencia del error basándose en su velocidad de cambio.
- **Fórmula:** $D = K_d \times \frac{\text{error actual} - \text{error anterior}}{\Delta t}$
- **Efecto:** Actúa como un "amortiguador". Si el robot se está acercando muy rápido a la pared, el término D nota ese cambio rápido y aplica una fuerza contraria para frenar el movimiento y evitar que el robot choque o se pase de largo.

---

## Implementación en el Robot

La corrección total es la suma de los tres términos:
$$\text{Corrección Total} = P + I + D$$

### Mezcla de Motores (Motor Mixing)
Para que el robot gire y corrija su trayectoria, aplicamos la corrección de forma diferencial:

```python
pwm_izq = base_speed + correccion
pwm_der = base_speed - correccion
```

- Si la **corrección es positiva** (estamos muy lejos de la pared): El motor izquierdo acelera y el derecho frena, haciendo que el robot gire hacia la derecha (hacia la pared).
- Si la **corrección es negativa** (estamos muy cerca): El motor derecho acelera y el izquierdo frena, alejando al robot de la pared.

---

## Guía de Ajuste (Tuning)

Si quieres ajustar el comportamiento del robot desde la interfaz web, sigue este orden:

1.  **Ajusta $K_p$ (Proporcional):** Empieza con $K_i$ y $K_d$ en 0. Aumenta $K_p$ hasta que el robot empiece a oscilar ligeramente alrededor de la distancia objetivo.
2.  **Ajusta $K_d$ (Derivativo):** Aumenta $K_d$ para eliminar las oscilaciones. Esto hará que el robot se mueva de forma más suave y "frenada".
3.  **Ajusta $K_i$ (Integral):** Si notas que el robot se queda estable pero siempre a una distancia un poco diferente a la del setpoint (ej. se queda a 17cm cuando pediste 15cm), aumenta un poco $K_i$ para corregir ese error residual.

## Seguridad Adicional
En nuestra implementación (`pid.py`), hemos añadido:
- **Evitación de Obstáculos:** Si el sensor frontal detecta algo a menos de 15cm, el robot reduce su `base_speed` automáticamente para evitar colisiones.
- **Watchdog:** Si el Python deja de enviar comandos, el Arduino detiene los motores en 500ms.

