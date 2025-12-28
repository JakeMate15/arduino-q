#include <Arduino_LED_Matrix.h>
#include <Arduino_RouterBridge.h>

Arduino_LED_Matrix matrix;

const uint32_t heart[] = { 0x3184a444, 0x44444208, 0x1100a004 };
const uint32_t danger[] = { 0x30c18c30, 0x6180c30c, 0x18c30c18 };

// === MOTORES ===
#define DIR_A 2 
#define PWM_A 5
#define DIR_B 4 
#define PWM_B 6
const bool MOTOR_B_INVERTIDO = true;

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

// === ULTRASÓNICOS ===
#define TRIG_DER 10
#define ECHO_DER 11
#define TRIG_CENTRO 12
#define ECHO_CENTRO 13
#define VEL_SONIDO 0.035103f

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
  unsigned long dur = pulseIn(echo, HIGH, 30000); 
  if (dur == 0) return -1.0f;
  return (dur * VEL_SONIDO) * 0.5f;
}

// Función para controlar motores desde Python
void controlar_motores(int vI, int vD) {
  // Determinamos dirección basado en signo del PWM
  int dirA = (vI >= 0) ? 1 : 0;
  int dirB = (vD >= 0) ? 1 : 0;
  avanza(abs(vI), abs(vD), dirA, dirB);
}

void setup() {
  Serial.begin(115200);
  matrix.begin();
  
  // --- Configuración Motores ---
  pinMode(DIR_A, OUTPUT);
  pinMode(DIR_B, OUTPUT);
  // Nota: No configuramos pinMode para PWM_A y PWM_B para que analogWrite funcione mejor
  
  // PRUEBA DE MOTORES: Girar 1 segundo al iniciar
  matrix.loadFrame(heart);
  Serial.println("Prueba de motores iniciada...");
  avanza(100, 100, 1, 1); // Velocidad reducida para prueba
  delay(1000);
  avanza(0, 0, 0, 0);     // Detener
  Serial.println("Prueba de motores terminada.");

  // --- Configuración Sensores ---
  pinMode(TRIG_CENTRO, OUTPUT);
  pinMode(ECHO_CENTRO, INPUT);
  pinMode(TRIG_DER, OUTPUT);
  pinMode(ECHO_DER, INPUT);

  digitalWrite(TRIG_CENTRO, LOW);
  digitalWrite(TRIG_DER, LOW);

  Bridge.begin();
  // Registrar función para recibir comandos de Python
  Bridge.provide("motores", controlar_motores);
  delay(1000);
}

void loop() {
  float dC = distanciaCM(TRIG_CENTRO, ECHO_CENTRO);
  float dR = distanciaCM(TRIG_DER, ECHO_DER);

  // Informar a Python las distancias medidas
  Bridge.notify("distancias", -1.0f, dC, dR);

  delay(20); // Ciclo rápido de 50Hz
}
