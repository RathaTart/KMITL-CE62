#define  BUTTON_RED_PIN 4
#define RED_PIN 12
#define  BUTTON_YELLOW_PIN 3
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


}

void loop() {
  // put your main code here, to run repeatedly:

  if(digitalRead(BUTTON_RED_PIN) == HIGH)
  {
    digitalWrite(RED_PIN, BUTTON1);
    BUTTON1 = !BUTTON1;
    delay(300);
  }

  if(digitalRead(BUTTON_YELLOW_PIN) == LOW)
  {
    digitalWrite(YELLOW_PIN, BUTTON2);
    BUTTON2 = !BUTTON2;
    delay(300);
  }

  if(digitalRead(BUTTON_GREEN_PIN) == LOW)
  {
    digitalWrite(GREEN_PIN, BUTTON3);
    BUTTON3 = !BUTTON3;
    delay(300);
  }

}

