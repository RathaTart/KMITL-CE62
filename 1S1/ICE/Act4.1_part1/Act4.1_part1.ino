#define  BUTTON_RED_PIN 3
#define RED_PIN 13
#define  BUTTON_YELLOW_PIN 4 
#define YELLOW_PIN 12
#define  BUTTON_GREEN_PIN 2
#define GREEN_PIN 11

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
    digitalWrite(RED_PIN, HIGH);
  }


  if(digitalRead(BUTTON_YELLOW_PIN) == LOW)
  {
    digitalWrite(YELLOW_PIN, HIGH);
  }

  if(digitalRead(BUTTON_GREEN_PIN) == LOW)
  { 
    digitalWrite(GREEN_PIN, HIGH);
  }

}
