#include <ArduinoBLE.h>

BLEService robotService("12345678-1234-1234-1234-1234567890ab");
BLEStringCharacteristic commandChar("abcd", BLEWrite, 20);

const int LED = LED_BUILTIN;

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
      // Se recibió algo: parpadeo rápido
      blink(2, 60, 60);

      String cmd = commandChar.value();
      cmd.trim();

      if (cmd == "avanza") {
        // Pulso largo
        digitalWrite(LED, LOW); delay(80);
        digitalWrite(LED, HIGH); delay(1000);
        // moverAdelante();
      } else if (cmd == "para") {
        // 2 pulsos cortos
        blink(2, 1000, 1000);
        // detener();
      } else {
        // 3 pulsos: desconocido
        blink(3, 1000, 1000);
      }

      // Volver a estado conectado (LED fijo)
      digitalWrite(LED, HIGH);
    }

    delay(10);
  }

  // Desconectado: apagar LED y volver a anunciar/idle
  digitalWrite(LED, LOW);
  delay(100);
}
