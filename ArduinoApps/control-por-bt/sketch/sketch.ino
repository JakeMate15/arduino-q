#include <ArduinoBLE.h>

BLEService robotService("12345678-1234-1234-1234-1234567890ab");
BLEStringCharacteristic commandChar("abcd", BLEWrite, 20);

const int LED = LED_BUILTIN;

// === MOTORES ===
#define DIR_A 2
#define PWM_A 5
#define DIR_B 4
#define PWM_B 6
const bool MOTOR_B_INVERTIDO = true;
const int VELOCIDAD_BASE = 100;

// === ULTRASÓNICO ===
#define TRIG_CENTRO 12
#define ECHO_CENTRO 13
const float VEL_SONIDO = 0.035103f;
const float DISTANCIA_SEGURA = 20.0f;

float distanciaCM() {
  digitalWrite(TRIG_CENTRO, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_CENTRO, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_CENTRO, LOW);

  unsigned long dur = pulseIn(ECHO_CENTRO, HIGH, 25000);
  if (dur == 0) return -1.0f;
  return (dur * VEL_SONIDO) / 2.0f;
}

bool es_seguro_avanzar() {
  float dist = distanciaCM();
  return (dist < 0 || dist >= DISTANCIA_SEGURA);
}

void mover_motores(int velA, int velB, int dirA, int dirB) {
  digitalWrite(DIR_A, dirA);
  digitalWrite(DIR_B, MOTOR_B_INVERTIDO ? (dirB ^ 1) : dirB);
  analogWrite(PWM_A, velA);
  analogWrite(PWM_B, velB);
}

void avanzar(int tiempo_ms) {
  if (!es_seguro_avanzar()) {
    mover_motores(0, 0, 0, 0);
    return;
  }

  mover_motores(VELOCIDAD_BASE, VELOCIDAD_BASE, 1, 1);
  delay(tiempo_ms);
  mover_motores(0, 0, 0, 0);
}

void retroceder(int tiempo_ms) {
  mover_motores(VELOCIDAD_BASE, VELOCIDAD_BASE, 0, 0);
  delay(tiempo_ms);
  mover_motores(0, 0, 0, 0);
}

void girar(int tiempo_ms) {
  mover_motores(VELOCIDAD_BASE, VELOCIDAD_BASE, 1, 0);
  delay(tiempo_ms);
  mover_motores(0, 0, 0, 0);
}

void blink(int times, int on_ms, int off_ms) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED, HIGH);
    delay(on_ms);
    digitalWrite(LED, LOW);
    delay(off_ms);
  }
}

void setup() {
  pinMode(LED, OUTPUT);
  digitalWrite(LED, LOW);

  // Configurar pines de motores
  pinMode(DIR_A, OUTPUT);
  pinMode(DIR_B, OUTPUT);

  // Configurar sensor ultrasónico
  pinMode(TRIG_CENTRO, OUTPUT);
  pinMode(ECHO_CENTRO, INPUT);

  // Señal de arranque
  blink(2, 150, 150);

  if (!BLE.begin()) {
    // Error: parpadeo rápido infinito
    while (1) {
      digitalWrite(LED, HIGH); delay(100);
      digitalWrite(LED, LOW);  delay(100);
    }
  }

  BLE.setLocalName("RobotUNOQ");
  BLE.setAdvertisedService(robotService);

  robotService.addCharacteristic(commandChar);
  BLE.addService(robotService);

  BLE.advertise();

  // Listo/anunciando: 1 parpadeo
  blink(1, 300, 300);
}

void loop() {
  BLE.poll();

  BLEDevice central = BLE.central();

  // Mientras NO haya conexión: parpadeo lento cada ~1s
  if (!central) {
    digitalWrite(LED, HIGH); delay(80);
    digitalWrite(LED, LOW);  delay(920);
    return;
  }

  // Conectado: LED fijo encendido
  digitalWrite(LED, HIGH);

  while (central.connected()) {
    BLE.poll();

    if (commandChar.written()) {
      String cmd = commandChar.value();
      cmd.trim();

      if (cmd == "avanza") {
        avanzar(1000);
      } else if (cmd == "retrocede") {
        retroceder(1000);
      } else if (cmd == "gira") {
        girar(1000);
      }
    }

    delay(10);
  }

  // Desconectado: apagar LED y volver a anunciar/idle
  digitalWrite(LED, LOW);
  delay(100);
}
