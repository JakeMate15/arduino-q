#include <Arduino_LED_Matrix.h>
#include <Arduino_RouterBridge.h>

Arduino_LED_Matrix matrix;
const uint32_t heart[] = { 0x3184a444, 0x44444208, 0x1100a004 };
const uint32_t off[] = { 0, 0, 0 };

// === MOTORES ===
#define DIR_A 2 
#define PWM_A 5
#define DIR_B 4 
#define PWM_B 6
const bool MOTOR_B_INVERTIDO = true;

// === ULTRASÓNICOS ===
#define TRIG_DER 10
#define ECHO_DER 11
#define TRIG_CENTRO 12
#define ECHO_CENTRO 13
const float VEL_SONIDO = 0.035103f;

// === SEGURIDAD (WATCHDOG) ===
unsigned long ultimoComandoTime = 0;
const unsigned long WATCHDOG_TIMEOUT = 500; // 500ms

int normPWM(int v) {
  return (v < 0) ? 0 : (v > 255) ? 255 : v;
}

void avanza(int velA, int velB, int dirA, int dirB) {
  digitalWrite(DIR_A, dirA);
  digitalWrite(DIR_B, MOTOR_B_INVERTIDO ? (dirB ^ 1) : dirB);
  analogWrite(PWM_A, normPWM(velA));
  analogWrite(PWM_B, normPWM(velB));
}

void controlar_motores(int vI, int vD) {
  int dirA = (vI >= 0) ? 1 : 0;
  int dirB = (vD >= 0) ? 1 : 0;
  avanza(abs(vI), abs(vD), dirA, dirB);
}

// Recibe valores X e Y del joystick (-255 a 255)
void recibir_joystick(int x, int y) {
  // Motor Mixing para dirección diferencial
  int vI = y + x;
  int vD = y - x;
  
  // Limitar a -255 a 255
  vI = max(-255, min(255, vI));
  vD = max(-255, min(255, vD));
  
  controlar_motores(vI, vD);
  ultimoComandoTime = millis(); // Reset watchdog
}

unsigned long pulseInManual(uint8_t pin, uint8_t state, unsigned long timeout) {
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
  unsigned long dur = pulseInManual(echo, HIGH, 25000); 
  if (dur == 0) return -1.0f;
  return (dur * VEL_SONIDO) / 2.0f;
}

void setup() {
  Bridge.begin();
  
  matrix.begin();
  matrix.loadFrame(heart);
  
  pinMode(DIR_A, OUTPUT);
  pinMode(DIR_B, OUTPUT);
  
  // Test inicial de motores
  avanza(100, 100, 1, 1);
  delay(300);
  avanza(0, 0, 0, 0);
  
  pinMode(TRIG_CENTRO, OUTPUT);
  pinMode(ECHO_CENTRO, INPUT);
  pinMode(TRIG_DER, OUTPUT);
  pinMode(ECHO_DER, INPUT);

  // Registrar el comando de joystick
  Bridge.provide("joystick", recibir_joystick);
  
  ultimoComandoTime = millis();
}

void loop() {
  // 1. Leer sensores y notificar al backend
  float dC = distanciaCM(TRIG_CENTRO, ECHO_CENTRO);
  float dR = distanciaCM(TRIG_DER, ECHO_DER);
  Bridge.notify("distancias", dC, dR);
  
  // 2. Watchdog de seguridad: Detener si no hay datos recientes
  if (millis() - ultimoComandoTime > WATCHDOG_TIMEOUT) {
    avanza(0, 0, 0, 0);
    matrix.loadFrame(off); // Indicar que está en espera/timeout
    delay(50);
    matrix.loadFrame(heart); // Parpadeo o similar
  } else {
    matrix.loadFrame(heart);
  }
  
  delay(50); // Frecuencia de ~20Hz para los sensores
}

