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

bool ejecutando_comando = false;

unsigned long pulseInManual(uint8_t pin, uint8_t state, unsigned long timeout) {
  unsigned long start = micros();
  while (digitalRead(pin) == state) { if (micros() - start > timeout) return 0; }
  while (digitalRead(pin) != state) { if (micros() - start > timeout) return 0; }
  unsigned long pulseStart = micros();
  while (digitalRead(pin) == state) { if (micros() - pulseStart > timeout) return 0; }
  return micros() - pulseStart;
}

float distanciaCM() {
  digitalWrite(TRIG_CENTRO, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_CENTRO, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_CENTRO, LOW);

  unsigned long dur = pulseInManual(ECHO_CENTRO, HIGH, 25000);
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
  ejecutando_comando = true;

  if (!es_seguro_avanzar()) {
    mover_motores(0, 0, 0, 0);
    ejecutando_comando = false;
    return;
  }

  mover_motores(VELOCIDAD_BASE, VELOCIDAD_BASE, 1, 1);
  delay(tiempo_ms);
  mover_motores(0, 0, 0, 0);

  ejecutando_comando = false;
}

void retroceder(int tiempo_ms) {
  ejecutando_comando = true;

  mover_motores(VELOCIDAD_BASE, VELOCIDAD_BASE, 0, 0);
  delay(tiempo_ms);
  mover_motores(0, 0, 0, 0);

  ejecutando_comando = false;
}

void girar(int tiempo_ms) {
  ejecutando_comando = true;

  mover_motores(VELOCIDAD_BASE, VELOCIDAD_BASE, 1, 0);
  delay(tiempo_ms);
  mover_motores(0, 0, 0, 0);

  ejecutando_comando = false;
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

  pinMode(DIR_A, OUTPUT);
  pinMode(DIR_B, OUTPUT);

  pinMode(TRIG_CENTRO, OUTPUT);
  pinMode(ECHO_CENTRO, INPUT);

  blink(2, 150, 150);

  if (!BLE.begin()) {
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

  blink(1, 300, 300);
}

void loop() {
  BLE.poll();

  BLEDevice central = BLE.central();

  if (!central) {
    digitalWrite(LED, HIGH); delay(80);
    digitalWrite(LED, LOW);  delay(920);
    return;
  }

  digitalWrite(LED, HIGH);

  while (central.connected()) {
    BLE.poll();

    if (commandChar.written() && !ejecutando_comando) {
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

  digitalWrite(LED, LOW);
  delay(100);
}
