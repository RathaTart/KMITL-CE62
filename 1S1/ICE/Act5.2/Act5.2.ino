#define Red1 11
#define Red2 10
#define Red3 9
#define Red4 8

void setup()
{
  Serial.begin(9600);
  pinMode(A0, INPUT);
  for (int i = 8; i <= 11; i++) {
    pinMode(i, OUTPUT);
    digitalWrite(i, LOW);
  }
}
  
void loop() 
{
  int sensorValue = analogRead(A0);
  float voltage = sensorValue * (5.0 / 1023.0);
  if (voltage > 3.3 && voltage < 3.5) {
    digitalWrite(Red1, HIGH);
  }
  else if (voltage > 4.8 && voltage < 6.0) {
    digitalWrite(Red2, HIGH);
  }
  else if (voltage > 4.4 && voltage < 4.6) {
    digitalWrite(Red3, HIGH);
  }
  else if (voltage > 2.4 && voltage < 2.6) {
    digitalWrite(Red4, HIGH);
  }
  else
  {
    digitalWrite(Red1, LOW);
    digitalWrite(Red2, LOW);
    digitalWrite(Red3, LOW);
    digitalWrite(Red4, LOW);
  }
  Serial.println(voltage);
}