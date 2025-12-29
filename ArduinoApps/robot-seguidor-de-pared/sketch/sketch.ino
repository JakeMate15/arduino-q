#include <Arduino_RouterBridge.h>

// === MOTORES ===
#define DIRA 2
#define DIRB 5
#define PWMA 4
#define PWMB 6

const bool INV_A = false;
const bool INV_B = true;

int limitar(int v, int lo, int hi){
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

// v en rango [-255..255]. signo = dirección
void motorA(int v){
  v = limitar(v, -255, 255);
  bool forward = (v >= 0);
  int pwm = abs(v);

  if (INV_A) forward = !forward;

  digitalWrite(DIRA, forward ? HIGH : LOW);
  analogWrite(PWMA, pwm);
}

void motorB(int v){
  v = limitar(v, -255, 255);
  bool forward = (v >= 0);
  int pwm = abs(v);

  if (INV_B) forward = !forward;

  digitalWrite(DIRB, forward ? HIGH : LOW);
  analogWrite(PWMB, pwm);
}

void motores(int vA, int vB){
  motorA(vA);
  motorB(vB);
}

void detener(){
  motores(0, 0);
}

void adelante(int pwm){
  pwm = limitar(pwm, 0, 255);
  motores(pwm, pwm);
}

void atras(int pwm){
  pwm = limitar(pwm, 0, 255);
  motores(-pwm, -pwm);
}

void curvaIzq(int base, int delta){
  base = limitar(base, 0, 255);
  delta = limitar(delta, 0, 255);
  motores(base - delta, base + delta);
}

void curvaDer(int base, int delta){
  base = limitar(base, 0, 255);
  delta = limitar(delta, 0, 255);
  motores(base + delta, base - delta);
}

void rotarIzq(int pwm){
  pwm = limitar(pwm, 0, 255);
  motores(-pwm, +pwm);
}

void rotarDer(int pwm){
  pwm = limitar(pwm, 0, 255);
  motores(+pwm, -pwm);
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

  detener();
}

void loop() {
  // Medición de sensores
  float dC = distanciaCM_mediana(TRIG_CENTRO, ECHO_CENTRO);
  delay(50);
  float dR = distanciaCM_mediana(TRIG_DER, ECHO_DER);
  Bridge.notify("distancias", dC, dR);

  // Pruebas de movimiento
  adelante(120);
  delay(1000);
  detener();
  delay(300);

  curvaIzq(120, 40);
  delay(1000);
  detener();
  delay(300);

  curvaDer(120, 40);
  delay(1000);
  detener();
  delay(300);

  rotarIzq(90);
  delay(700);
  detener();
  delay(800);
}
