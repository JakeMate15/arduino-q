// === ULTRASÓNICOS ===
#define TRIG_DER 10
#define ECHO_DER 11
#define TRIG_CENTRO 12
#define ECHO_CENTRO 13
const float VEL_SONIDO = 0.035103f;

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

  pinMode(TRIG_CENTRO, OUTPUT);
  pinMode(ECHO_CENTRO, INPUT);
  pinMode(TRIG_DER, OUTPUT);
  pinMode(ECHO_DER, INPUT);

}

void loop() {
  float dC = distanciaCM(TRIG_CENTRO, ECHO_CENTRO);
  float dR = distanciaCM(TRIG_DER, ECHO_DER);

  Bridge.notify("distancias", dC, dR);

  delay(20);
}
