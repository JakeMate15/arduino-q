#include <Arduino_LED_Matrix.h>
#include <Arduino_RouterBridge.h>

Arduino_LED_Matrix matrix;
const uint32_t heart[] = { 0x3184a444, 0x44444208, 0x1100a004 };

#define DIR_A 2 
#define PWM_A 5
#define DIR_B 4 
#define PWM_B 6
const bool MOTOR_B_INVERTIDO = true;

#define TRIG_DER 10
#define ECHO_DER 11
#define TRIG_CENTRO 12
#define ECHO_CENTRO 13
const float VEL_SONIDO = 0.035103f;

int normPWM(int v) {
  return (v < 0) ? 0 : (v > 255) ? 255 : v;
}

void avanza(int velA, int velB, int dirA, int dirB) {
  digitalWrite(DIR_A, dirA);
  digitalWrite(DIR_B, MOTOR_B_INVERTIDO ? (dirB ^ 1) : dirB);
  analogWrite(PWM_A, normPWM(velA));
  analogWrite(PWM_B, normPWM(velB));
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

void controlar_motores(int vI, int vD) {
  int dirA = (vI >= 0) ? 1 : 0;
  int dirB = (vD >= 0) ? 1 : 0;
  avanza(abs(vI), abs(vD), dirA, dirB);
}

void setup() {
  Bridge.begin();
  
  matrix.begin();
  matrix.loadFrame(heart);
  
  pinMode(DIR_A, OUTPUT);
  pinMode(PWM_A, OUTPUT);
  pinMode(DIR_B, OUTPUT);
  pinMode(PWM_B, OUTPUT);
  
  pinMode(TRIG_CENTRO, OUTPUT);
  pinMode(ECHO_CENTRO, INPUT);
  pinMode(TRIG_DER, OUTPUT);
  pinMode(ECHO_DER, INPUT);

  Bridge.provide("motores", controlar_motores);
}

void loop() {
  float dC = distanciaCM(TRIG_CENTRO, ECHO_CENTRO);
  float dR = distanciaCM(TRIG_DER, ECHO_DER);
  Bridge.notify("distancias", -1.0f, dC, dR);
  delay(50);
}