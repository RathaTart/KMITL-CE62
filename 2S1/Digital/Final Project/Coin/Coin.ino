int sensor = 23;
int led = 22;
int i = 0;
int c = 0;
volatile bool isCounter = false;
volatile int count = 0;
unsigned long lastInterruptTime = 0; // For debouncing

void IRAM_ATTR doCounter() {
  unsigned long interruptTime = millis();
  // Simple debounce mechanism to avoid multiple triggers within 200ms
  if (interruptTime - lastInterruptTime > 200) {
    isCounter = true;
    count++;
    lastInterruptTime = interruptTime;
  }
}

void setup() {
  pinMode(sensor, INPUT);
  pinMode(led, OUTPUT);
  attachInterrupt(digitalPinToInterrupt(sensor), doCounter, FALLING);
  Serial.begin(9600);
}

void loop() {
  if (isCounter) {
    isCounter = false;
    if (count > 1) {
      i += 1;
      Serial.print("จำนวนเหรียญ : ");
      Serial.println(i);
      c = i * 10;
      Serial.print("จำนวนเงิน : ");
      Serial.print(c);
      Serial.println(" บาท");
      delay(1000);
      count = 0;
    }
    if (c == 20) {
      c -= 20;
      i -= 2;
      digitalWrite(led, HIGH);
      Serial.println();
      Serial.print("ระบบทำงาน\nLED ON\n\n");
      delay(10000);
      Serial.print("เคลียร์เหรียญ / จำนวนเงิน\nจำนวนเหรียญ : ");
      Serial.println(i);
      Serial.print("จำนวนเงิน : ");
      Serial.print(c);
      Serial.println(" บาท\nหยุดการทำงานของระบบ\nLED OFF\n\n");
      digitalWrite(led, LOW);
    }
  }
}
