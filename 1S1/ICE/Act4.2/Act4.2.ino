#define  BUTTON_RED_PIN 3
#define RED_PIN 12
#define  BUTTON_YELLOW_PIN 4
#define YELLOW_PIN 11
#define  BUTTON_GREEN_PIN 2
#define GREEN_PIN 10
int BUTTON1 = HIGH;
int BUTTON2 = HIGH;
int BUTTON3 = HIGH;

void setup() {
  // put your setup code here, to run once:
  //Serial.begin(9600);
  pinMode(BUTTON_RED_PIN, INPUT);
  pinMode(RED_PIN, OUTPUT);
  pinMode(BUTTON_YELLOW_PIN, INPUT);
  pinMode(YELLOW_PIN, OUTPUT);
  pinMode(BUTTON_GREEN_PIN, INPUT_PULLUP);
  pinMode(GREEN_PIN, OUTPUT);

  attachInterrupt(1, ISR1, RISING);
  attachInterrupt(0, ISR2, RISING);

}

void loop() {
  // put your main code here, to run repeatedly:

  digitalWrite(GREEN_PIN, HIGH);
  digitalWrite(RED_PIN, LOW);
  delay(7000);
  digitalWrite(RED_PIN, LOW);
  digitalWrite(GREEN_PIN, LOW);
  digitalWrite(YELLOW_PIN, HIGH);
  delay(250);
  digitalWrite(YELLOW_PIN, LOW);
  
  delay(250);
  digitalWrite(YELLOW_PIN, HIGH);

  delay(250);
  digitalWrite(YELLOW_PIN, LOW);
;
  delay(250);
  digitalWrite(YELLOW_PIN, HIGH);

  delay(250);
  digitalWrite(YELLOW_PIN, LOW);

  delay(250);
  digitalWrite(YELLOW_PIN, HIGH);

  delay(250);
  digitalWrite(YELLOW_PIN, LOW);

  delay(250);
  digitalWrite(YELLOW_PIN, HIGH);

  delay(250);
  digitalWrite(YELLOW_PIN, LOW);

  delay(250);
  digitalWrite(YELLOW_PIN, HIGH);

  delay(250);
  digitalWrite(YELLOW_PIN, LOW);

  delay(250);
  digitalWrite(RED_PIN, HIGH);
  delay(5000);
  digitalWrite(RED_PIN, LOW);
}

void ISR1()
{
  digitalWrite(RED_PIN, HIGH);
  digitalWrite(YELLOW_PIN, LOW);
  digitalWrite(GREEN_PIN, LOW);
  delay(5000);
}

void ISR2()
{
  digitalWrite(YELLOW_PIN, LOW);
  digitalWrite(GREEN_PIN, LOW);
  digitalWrite(RED_PIN, LOW);  
  delay(5000);
}

