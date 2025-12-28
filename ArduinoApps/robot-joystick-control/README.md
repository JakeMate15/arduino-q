# Robot Joystick Control

Esta aplicación permite controlar un robot de dos motores (tracción diferencial) mediante un joystick en una interfaz web.

## Características

- Control en tiempo real mediante un joystick táctil (nipplejs).
- Visualización de la potencia (PWM) enviada a cada motor.
- Visualización de la distancia medida por los sensores ultrasónicos (frontal y derecho).
- Watchdog de seguridad en el Arduino (detiene los motores si se pierde la conexión).
- **Modo Recolección de Datos para IA**: Sistema de grabación CSV para entrenar redes neuronales.

## Recolección de Datos para Entrenamiento IA

Esta aplicación incluye un sistema de grabación de datos diseñado para entrenar modelos de aprendizaje automático.

### ¿Cómo funciona?

1. **Activa el interruptor REC** en la interfaz web (parte superior derecha).
2. **Conduce el robot** normalmente usando el joystick o los botones de giro.
3. **Los datos se guardan automáticamente** en un archivo CSV mientras el robot se mueve.

### ¿Dónde se guardan los datos?

El archivo `recorrido_robot.csv` se guarda en:
```
ArduinoApps/robot-joystick-control/python/recorrido_robot.csv
```

### Formato de los Datos

El archivo CSV contiene las siguientes columnas:

| Columna | Descripción | Ejemplo |
|---------|-------------|---------|
| `timestamp` | Fecha y hora ISO del registro | `2025-12-28T16:30:45.123456` |
| `dist_frontal` | Distancia del sensor frontal (cm) | `15.2` |
| `dist_derecho` | Distancia del sensor derecho (cm) | `20.1` |
| `pwm_izq` | Velocidad del motor izquierdo (-150 a 150) | `110` |
| `pwm_der` | Velocidad del motor derecho (-150 a 150) | `108` |

### Características de la Grabación

- **Frecuencia de muestreo**: ~50Hz (cada 20ms)
- **Filtrado inteligente**: Solo se guardan datos cuando el robot está en movimiento (evita datos estáticos)
- **Append mode**: Los datos se añaden al archivo existente, permitiendo múltiples sesiones de entrenamiento
- **Logging**: El sistema registra en los logs la ubicación del archivo al iniciar

### Uso para Entrenamiento

1. Realiza múltiples sesiones de conducción variando:
   - Rectas largas
   - Giros de 90 grados
   - Correcciones sutiles (acercarse y alejarse de paredes)
   - Movimientos fluidos (evita movimientos bruscos)

2. El archivo CSV resultante puede ser usado directamente con bibliotecas como:
   - TensorFlow / Keras
   - PyTorch
   - scikit-learn
   - Pandas (para análisis previo)

3. **Ubicación del archivo**: Revisa los logs de la aplicación al iniciar para ver la ruta exacta del archivo CSV.

## Requisitos de Hardware

- Arduino UNO R4 WiFi (o compatible con Bridge).
- Driver de motores L298N o similar.
- 2 Motores DC.
- 2 Sensores Ultrasónicos HC-SR04.

### Conexiones (Pines por defecto)

- **Motores:**
  - Motor Izquierdo: DIR=2, PWM=5
  - Motor Derecho: DIR=4, PWM=6
- **Sensores:**
  - Frontal: Trig=12, Echo=13
  - Derecho: Trig=10, Echo=11

## Instalación

1. Sube el sketch a tu Arduino.
2. Ejecuta la aplicación desde el panel de Arduino Q.
3. Abre la interfaz web para empezar a controlar el robot.

