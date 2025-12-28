# Robot Joystick Control

Esta aplicación permite controlar un robot de dos motores (tracción diferencial) mediante un joystick en una interfaz web.

## Características

- Control en tiempo real mediante un joystick táctil (nipplejs).
- Visualización de la potencia (PWM) enviada a cada motor.
- Visualización de la distancia medida por los sensores ultrasónicos (frontal y derecho).
- Watchdog de seguridad en el Arduino (detiene los motores si se pierde la conexión).

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

