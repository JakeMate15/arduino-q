#include <Arduino_RouterBridge.h>

// === MOTORES ===
#define DIRA 2
#define DIRB 3
#define PWMA 5
#define PWMB 6

const bool INV_A = false;  // pon true si el lado A va al revés
const bool INV_B = false;  // pon true si el lado B va al revés

int clampi(int v, int lo, int hi){
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

// v en rango [-255..255]. signo = dirección
void setMotorA(int v){
  v = clampi(v, -255, 255);
  bool forward = (v >= 0);
  int pwm = abs(v);

  if (INV_A) forward = !forward;

  digitalWrite(DIRA, forward ? HIGH : LOW);
  analogWrite(PWMA, pwm);
}

void setMotorB(int v){
  v = clampi(v, -255, 255);
  bool forward = (v >= 0);
  int pwm = abs(v);

  if (INV_B) forward = !forward;

  digitalWrite(DIRB, forward ? HIGH : LOW);
  analogWrite(PWMB, pwm);
}

void setDrive(int vA, int vB){
  setMotorA(vA);
  setMotorB(vB);
}

void stopRobot(){
  setDrive(0, 0);
}

void forward(int pwm){
  pwm = clampi(pwm, 0, 255);
  setDrive(pwm, pwm);
}

void backward(int pwm){
  pwm = clampi(pwm, 0, 255);
  setDrive(-pwm, -pwm);
}

void turnLeftArc(int base, int delta){
  base  = clampi(base, 0, 255);
  delta = clampi(delta, 0, 255);
  setDrive(base - delta, base + delta);
}

void turnRightArc(int base, int delta){
  base  = clampi(base, 0, 255);
  delta = clampi(delta, 0, 255);
  setDrive(base + delta, base - delta);
}

void pivotLeft(int pwm){
  pwm = clampi(pwm, 0, 255);
  setDrive(-pwm, +pwm);
}

void pivotRight(int pwm){
  pwm = clampi(pwm, 0, 255);
  setDrive(+pwm, -pwm);
}

// === ULTRASÓNICOS ===
#define TRIG_DER 10
#define ECHO_DER 11
#define TRIG_CENTRO 12
#define ECHO_CENTRO 13
const float VEL_SONIDO = 0.035103f;
const float SIN_ECO = 400.0f;

unsigned long pulseHighManual(uint8_t pin, unsigned long timeout_us) {
  unsigned long t0 = micros();

  while (digitalRead(pin) == HIGH) {
    if (micros() - t0 > timeout_us) return 0;
  }

  while (digitalRead(pin) == LOW) {
    if (micros() - t0 > timeout_us) return 0;
  }

  unsigned long t1 = micros();
  while (digitalRead(pin) == HIGH) {
    if (micros() - t1 > timeout_us) return 0;
  }

  return micros() - t1;
}

float distanciaCM(int trig, int echo) {
  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);
  unsigned long dur = pulseHighManual(echo, 25000);
  if (dur == 0) return SIN_ECO;
  return (dur * VEL_SONIDO) / 2.0f;
}

float median3(float a, float b, float c) {
  if ((a <= b && b <= c) || (c <= b && b <= a)) return b;
  if ((b <= a && a <= c) || (c <= a && a <= b)) return a;
  return c;
}

float distanciaCM_mediana(int trig, int echo) {
  float a = distanciaCM(trig, echo);
  delay(10);
  float b = distanciaCM(trig, echo);
  delay(10);
  float c = distanciaCM(trig, echo);
  return median3(a, b, c);
}

void setup() {
  Bridge.begin();

  // Sensores
  pinMode(TRIG_CENTRO, OUTPUT);
  pinMode(ECHO_CENTRO, INPUT);
  pinMode(TRIG_DER, OUTPUT);
  pinMode(ECHO_DER, INPUT);

  // Motores
  pinMode(DIRA, OUTPUT);
  pinMode(DIRB, OUTPUT);
  pinMode(PWMA, OUTPUT);
  pinMode(PWMB, OUTPUT);

  stopRobot();
}

void loop() {
  float dC = distanciaCM_mediana(TRIG_CENTRO, ECHO_CENTRO);
  delay(50);
  float dR = distanciaCM_mediana(TRIG_DER, ECHO_DER);
  Bridge.notify("distancias", dC, dR);

  delay(80);
}
