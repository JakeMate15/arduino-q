#include <Arduino_RouterBridge.h>

// === MOTORES ===
#define DIR_A 2 
#define PWM_A 5
#define DIR_B 4 
#define PWM_B 6
const bool MOTOR_B_INVERTIDO = true;

int limitar(int v, int lo, int hi){
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

void avanza(int velA, int velB, int dirA, int dirB) {
  digitalWrite(DIR_A, dirA ? HIGH : LOW);
  bool dB = dirB ? true : false;
  if (MOTOR_B_INVERTIDO) dB = !dB;
  digitalWrite(DIR_B, dB ? HIGH : LOW);

  analogWrite(PWM_A, limitar(velA, 0, 255));
  analogWrite(PWM_B, limitar(velB, 0, 255));
}

void motores(int vI, int vD) {
  vI = limitar(vI, -255, 255);
  vD = limitar(vD, -255, 255);
  avanza(abs(vI), abs(vD), (vI >= 0), (vD >= 0));
}

void detener(){
  motores(0, 0);
}

void adelante(int pwm){
  motores(pwm, pwm);
}

void atras(int pwm){
  motores(-pwm, -pwm);
}

void curvaIzq(int base, int delta){
  int vI = limitar(base - delta, 0, 255);
  int vD = limitar(base + delta, 0, 255);
  motores(vI, vD);
}

void curvaDer(int base, int delta){
  int vI = limitar(base + delta, 0, 255);
  int vD = limitar(base - delta, 0, 255);
  motores(vI, vD);
}

void rotarIzq(int pwm){
  motores(-pwm, pwm);
}

void rotarDer(int pwm){
  motores(pwm, -pwm);
}

void esperaParado(int ms){
  detener();
  delay(ms);
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
  pinMode(DIR_A, OUTPUT);
  pinMode(DIR_B, OUTPUT);

  // Test rápido de motores al arrancar
  motores(150, 150);
  delay(200);
  detener();

  detener();
}

// void loop() {
//   float dC = distanciaCM_mediana(TRIG_CENTRO, ECHO_CENTRO);
//   delay(50); // evita interferencia
//   float dR = distanciaCM_mediana(TRIG_DER, ECHO_DER);

//   // Notificar a Python
//   Bridge.notify("distancias", dC, dR);

//   if (dC < 25) detener();
//   else adelante(180);

//   delay(50); // ~10 Hz
// }
void loop() {
  // // 1) Adelante
  // adelante(150);
  // delay(1000);
  // esperaParado(400);

  // // 2) Atrás
  // atras(150);
  // delay(800);
  // esperaParado(400);

  // // 3) Curva izquierda (arco)
  // // base = velocidad promedio, delta = cuánto gira
  // curvaIzq(150, 50);
  // delay(1200);
  // esperaParado(400);

  // // 4) Curva derecha (arco)
  // curvaDer(150, 50);
  // delay(1200);
  // esperaParado(400);

  // // 5) Rotar izquierda (en el lugar)
  // rotarIzq(120);
  // delay(800);
  // esperaParado(500);

  // // 6) Rotar derecha (en el lugar)
  // rotarDer(120);
  // delay(800);
  // esperaParado(800);

  rotarDer(150);
  delay(400);
  esperaParado(800);
}