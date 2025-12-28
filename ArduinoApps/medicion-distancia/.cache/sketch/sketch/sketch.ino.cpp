#include <Arduino.h>
#line 1 "/home/arduino/ArduinoApps/medicion-distancia/sketch/sketch.ino"
#include <Arduino_LED_Matrix.h>
#include <Arduino_RouterBridge.h>

Arduino_LED_Matrix matrix;

const uint32_t heart[] = {
  0x3184a444,
  0x44444208,
  0x1100a004
};

// === MOTORES ===
#define DIR_A 2 
#define PWM_A 5

#define DIR_B 4 
#define PWM_B 6

const bool MOTOR_B_INVERTIDO = true;

#line 21 "/home/arduino/ArduinoApps/medicion-distancia/sketch/sketch.ino"
int normPWM(int v);
#line 27 "/home/arduino/ArduinoApps/medicion-distancia/sketch/sketch.ino"
void avanza(int velA, int velB, int dirA, int dirB);
#line 49 "/home/arduino/ArduinoApps/medicion-distancia/sketch/sketch.ino"
unsigned long pulseIn(uint8_t pin, uint8_t state, unsigned long timeout);
#line 58 "/home/arduino/ArduinoApps/medicion-distancia/sketch/sketch.ino"
float distanciaCM(int trig, int echo);
#line 69 "/home/arduino/ArduinoApps/medicion-distancia/sketch/sketch.ino"
void setup();
#line 99 "/home/arduino/ArduinoApps/medicion-distancia/sketch/sketch.ino"
void loop();
#line 21 "/home/arduino/ArduinoApps/medicion-distancia/sketch/sketch.ino"
int normPWM(int v) {
  if (v < 0)   return 0;
  if (v > 255) return 255;
  return (int)v;
}

void avanza(int velA, int velB, int dirA, int dirB) {
  int vA = normPWM(velA);
  int vB = normPWM(velB);

  int dirB_real = MOTOR_B_INVERTIDO ? (dirB ^ 1) : dirB;

  digitalWrite(DIR_A, dirA);
  digitalWrite(DIR_B, dirB_real);
  analogWrite(PWM_A, vA);
  analogWrite(PWM_B, vB);
}

// === ULTRASÓNICOS (HC-SR04) ===
#define TRIG_IZQ 122
#define ECHO_IZQ 112
#define TRIG_DER 10
#define ECHO_DER 11
#define TRIG_CENTRO 12
#define ECHO_CENTRO 13
#define VEL_SONIDO 0.035103f

// Implementación manual de pulseIn para Zephyr
unsigned long pulseIn(uint8_t pin, uint8_t state, unsigned long timeout) {
    unsigned long start = micros();
    while (digitalRead(pin) == state) { if (micros() - start > timeout) return 0; }
    while (digitalRead(pin) != state) { if (micros() - start > timeout) return 0; }
    unsigned long pulseStart = micros();
    while (digitalRead(pin) == state) { if (micros() - pulseStart > timeout) return 0; }
    return micros() - pulseStart;
}

float distanciaCM(int trig, int echo) {
  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);
  unsigned long dur = pulseIn(echo, HIGH, 30000); // 30ms timeout (~5 metros max)
  if (dur == 0) return -1.0f;
  return (dur * VEL_SONIDO) * 0.5f;
}

void setup() {
  Serial.begin(115200);
  matrix.begin();
  
  // Motores
  pinMode(DIR_A, OUTPUT);
  pinMode(PWM_A, OUTPUT);
  pinMode(DIR_B, OUTPUT);
  pinMode(PWM_B, OUTPUT);

  // Sensores
  pinMode(TRIG_CENTRO, OUTPUT);
  pinMode(ECHO_CENTRO, INPUT);
  pinMode(TRIG_DER, OUTPUT);
  pinMode(ECHO_DER, INPUT);
  
  // Sensor izquierdo (preparado para uso futuro)
  // pinMode(TRIG_IZQ, OUTPUT);
  // pinMode(ECHO_IZQ, INPUT);

  digitalWrite(TRIG_CENTRO, LOW);
  digitalWrite(TRIG_DER, LOW);
  // digitalWrite(TRIG_IZQ, LOW);

  Bridge.begin();

  matrix.loadFrame(heart);
  delay(2000);
}

void loop() {  
  float dC = distanciaCM(TRIG_CENTRO, ECHO_CENTRO);
  float dR = distanciaCM(TRIG_DER, ECHO_DER);
  float dI = -1.0f; // Valor por defecto para sensor no conectado

  // Si decides habilitar el sensor izquierdo, descomenta la siguiente línea:
  // dI = distanciaCM(TRIG_IZQ, ECHO_IZQ);

  // Enviamos los datos a Python usando el patrón de notificación
  Bridge.notify("distancias", dI, dC, dR);

  // Parpadeo visual en la matriz de LEDs
  matrix.loadFrame(heart);
  delay(100);
  matrix.clear();
  delay(400); // Frecuencia total de ~0.5 segundos por lectura
}
