#define m1 7   //Right Motor MA1   FORWORD 7
#define m2 6   //Right Motor MA2   BACKWORD 6
#define m3 9   //Left Motor MB1    FORWORD 9
#define m4 8   //Left Motor MB2    BACKWORD 8
#define e1 5   //Right Motor Enable Pin EA
#define e2 10  //Left Motor Enable Pin EB

//**********5 Channel IR Sensor Connection**********//
#define ir1 A0  //Left
#define ir2 A1
#define ir3 A2
#define ir4 A3
#define ir5 A4  //Right
//*************************************************//
#define B1 585
#define B2 505
#define B3 660
#define B4 430
#define B5 500
#define W1 978
#define W2 978
#define W3 982
#define W4 973
#define W5 978
//***************************************************//
#define min1 30    //30
#define min2 55    //55
#define normal 80  //80
#define max1 105   //105
#define max2 130   //130

int sensor = A5;
int Wait = 5;
unsigned long time_now = 0;
int blackCount = 0;

void setup() {
  Serial.begin(9600);
  pinMode(m1, OUTPUT);
  pinMode(m2, OUTPUT);
  pinMode(m3, OUTPUT);
  pinMode(m4, OUTPUT);
  pinMode(e1, OUTPUT);
  pinMode(e2, OUTPUT);
  pinMode(ir1, INPUT);
  pinMode(ir2, INPUT);
  pinMode(ir3, INPUT);
  pinMode(ir4, INPUT);
  pinMode(ir5, INPUT);
  pinMode(sensor, INPUT);
}

void loop() {
  //Reading Sensor Values
  int s1 = analogRead(ir1);            //Left Most Sensor
  int s2 = analogRead(ir2);            //Left Sensor
  int s3 = analogRead(ir3);            //Middle Sensor
  int s4 = analogRead(ir4);            //Right Sensor
  int s5 = analogRead(ir5);            //Right Most Sensor
  int ValSensor = analogRead(sensor);  // 1 = No light, 0 = Light

  // Serial.print("Sensor = ");
  // Serial.println(analogRead(sensor));
  // delay(100);


  // BLACK 93 472 889 52 57
  // WHITE 410 969 980 328 480

  int Val1, Val2, Val3, Val4, Val5;
  Val1 = (B1 + W1) / 2;
  Val2 = (B2 + W2) / 2;
  Val3 = (B3 + W3) / 2;
  Val4 = (B4 + W4) / 2;
  Val5 = (B5 + W5) / 2;
  //Calculation
  if (s1 <= Val1) {
    s1 = 1;
  } else {
    s1 = 0;
  }
  if (s2 <= Val2) {
    s2 = 1;
  } else {
    s2 = 0;
  }
  if (s3 <= Val3) {
    s3 = 1;
  } else {
    s3 = 0;
  }
  if (s4 <= Val4) {
    s4 = 1;
  } else {
    s4 = 0;
  }
  if (s5 <= Val5) {
    s5 = 1;
  } else {
    s5 = 0;
  }

  Serial.print("A0 : ");
  Serial.print(s1);
  Serial.print("  A1 : ");
  Serial.print(s2);
  Serial.print("  A2 : ");
  Serial.print(s3);
  Serial.print("  A3 : ");
  Serial.print(s4);
  Serial.print("  A4 : ");
  Serial.println(s5);




  //if only middle sensor detects black line
  if ((s1 == 1) && (s2 == 1) && (s3 == 1) && (s4 == 1) && (s5 == 1)) {
    blackCount++;
    digitalWrite(m1, LOW);
    digitalWrite(m2, LOW);
    digitalWrite(m3, LOW);
    digitalWrite(m4, LOW);
    time_now = millis();
    int count = 0;
    while (millis() < time_now + (Wait * 1000)) 
    {
      //Serial.println(ValSensor);
      if (analogRead(sensor) <= 420) 
      {
        count++;
        if(count == 1)
        {
          time_now = millis();
        }
        Serial.print("count");
        Serial.println(count);
        Serial.println(analogRead(sensor));
        delay(1005);
      }
      if (count >= 2) 
      {
        Serial.println("More than 2");
        s1 = 0;
        s2 = 0;
        s3 = 1;
        s4 = 1;
        s5 = 1;
        break;
      }
    }
    if (count == 1) 
    {
      Serial.println("There is 1");
      s1 = 1;
      s2 = 1;
      s3 = 1;
      s4 = 0;
      s5 = 0;
    }
    if (blackCount > 2)
    {
      s1 = 0;
      s2 = 0;
      s3 = 1;
      s4 = 1;
      s5 = 1;
      blackCount = 0;
    }
  }
   Serial.println("OUT");
  if ((s1 == 0) && (s2 == 0) && (s3 == 1) && (s4 == 0) && (s5 == 0)) {
    analogWrite(e1, max1);
    analogWrite(e2, max1);
    digitalWrite(m1, HIGH);
    digitalWrite(m2, LOW);
    digitalWrite(m3, HIGH);
    digitalWrite(m4, LOW);
  }
  if ((s1 == 0) && (s2 == 1) && (s3 == 1) && (s4 == 1) && (s5 == 0)) {
    analogWrite(e1, max1);
    analogWrite(e2, max1);
    digitalWrite(m1, HIGH);
    digitalWrite(m2, LOW);
    digitalWrite(m3, HIGH);
    digitalWrite(m4, LOW);
  }
  if ((s1 == 0) && (s2 == 1) && (s3 == 1) && (s4 == 0) && (s5 == 0)) {
    analogWrite(e1, min2);  //55
    analogWrite(e2, max1);  //105
    digitalWrite(m1, HIGH);
    digitalWrite(m2, LOW);
    digitalWrite(m3, HIGH);
    digitalWrite(m4, LOW);
  }
  if ((s1 == 1) && (s2 == 1) && (s3 == 1) && (s4 == 0) && (s5 == 0)) {
    analogWrite(e1, min2);
    analogWrite(e2, max2);
    digitalWrite(m1, HIGH);
    digitalWrite(m2, LOW);
    digitalWrite(m3, HIGH);
    digitalWrite(m4, LOW);
    delay(250);
  }
  if ((s1 == 1) && (s2 == 1) && (s3 == 0) && (s4 == 0) && (s5 == 0)) {
    analogWrite(e1, min2);
    analogWrite(e2, max1);
    digitalWrite(m1, HIGH);
    digitalWrite(m2, LOW);
    digitalWrite(m3, HIGH);
    digitalWrite(m4, LOW);
  }
  if ((s1 == 1) && (s2 == 0) && (s3 == 0) && (s4 == 0) && (s5 == 0)) {
    analogWrite(e1, min2);
    analogWrite(e2, max2);
    digitalWrite(m1, HIGH);
    digitalWrite(m2, LOW);
    digitalWrite(m3, HIGH);
    digitalWrite(m4, LOW);
  }
  if ((s1 == 1) && (s2 == 0) && (s3 == 1) && (s4 == 0) && (s5 == 0)) {
    analogWrite(e1, min1);
    analogWrite(e2, max2);
    digitalWrite(m1, HIGH);
    digitalWrite(m2, LOW);
    digitalWrite(m3, HIGH);
    digitalWrite(m4, LOW);
    delay(1250);
  }
  if ((s1 == 0) && (s2 == 1) && (s3 == 0) && (s4 == 0) && (s5 == 0)) {
    analogWrite(e1, min1);
    analogWrite(e2, max2);
    digitalWrite(m1, HIGH);
    digitalWrite(m2, LOW);
    digitalWrite(m3, HIGH);
    digitalWrite(m4, LOW);
  }
  if ((s1 == 0) && (s2 == 0) && (s3 == 1) && (s4 == 1) && (s5 == 0)) {
    analogWrite(e1, max1);
    analogWrite(e2, min2);
    digitalWrite(m1, HIGH);
    digitalWrite(m2, LOW);
    digitalWrite(m3, HIGH);
    digitalWrite(m4, LOW);
  }
  if ((s1 == 0) && (s2 == 0) && (s3 == 1) && (s4 == 1) && (s5 == 1)) {
    analogWrite(e1, max2);
    analogWrite(e2, min1);
    digitalWrite(m1, HIGH);
    digitalWrite(m2, LOW);
    digitalWrite(m3, HIGH);
    digitalWrite(m4, LOW);
    delay(250);
  }
  if ((s1 == 0) && (s2 == 0) && (s3 == 0) && (s4 == 1) && (s5 == 1)) {
    analogWrite(e1, max2);
    analogWrite(e2, min2);
    digitalWrite(m1, HIGH);
    digitalWrite(m2, LOW);
    digitalWrite(m3, HIGH);
    digitalWrite(m4, LOW);
  }
  if ((s1 == 0) && (s2 == 0) && (s3 == 0) && (s4 == 0) && (s5 == 1)) {
    analogWrite(e1, max2);
    analogWrite(e2, min2);
    digitalWrite(m1, HIGH);
    digitalWrite(m2, LOW);
    digitalWrite(m3, HIGH);
    digitalWrite(m4, LOW);
  }
  if ((s1 == 0) && (s2 == 0) && (s3 == 1) && (s4 == 0) && (s5 == 1)) {
    analogWrite(e1, max2);
    analogWrite(e2, min1);
    digitalWrite(m1, HIGH);
    digitalWrite(m2, LOW);
    digitalWrite(m3, HIGH);
    digitalWrite(m4, LOW);
    delay(1250);
  }
  if ((s1 == 0) && (s2 == 0) && (s3 == 0) && (s4 == 1) && (s5 == 0)) {
    analogWrite(e1, max2);
    analogWrite(e2, min1);
    digitalWrite(m1, HIGH);
    digitalWrite(m2, LOW);
    digitalWrite(m3, HIGH);
    digitalWrite(m4, LOW);
  }
  // WHITE
  if ((s1 == 0) && (s2 == 0) && (s3 == 0) && (s4 == 0) && (s5 == 0)) {
    delay(200);
    if ((s1 == 1) || (s2 == 1) || (s3 == 1) || (s4 == 1) || (s5 == 1)) {
    } else {
      analogWrite(e1, normal);
      analogWrite(e2, normal);
      digitalWrite(m1, LOW);
      digitalWrite(m2, HIGH);
      digitalWrite(m3, LOW);
      digitalWrite(m4, HIGH);
    }
  }
  if ((s1 == 1) && (s2 == 0) && (s3 == 1) && (s4 == 0) && (s5 == 1)) {
    analogWrite(e1, max1);
    analogWrite(e2, max1);
    digitalWrite(m1, HIGH);
    digitalWrite(m2, LOW);
    digitalWrite(m3, HIGH);
    digitalWrite(m4, LOW);
  }
  if ((s1 == 1) && (s2 == 1) && (s3 == 0) && (s4 == 1) && (s5 == 1)) {
    analogWrite(e1, max1);
    analogWrite(e2, max1);
    digitalWrite(m1, HIGH);
    digitalWrite(m2, LOW);
    digitalWrite(m3, HIGH);
    digitalWrite(m4, LOW);
  }
  if ((s1 == 1) && (s2 == 0) && (s3 == 0) && (s4 == 0) && (s5 == 1)) {
    analogWrite(e1, max1);
    analogWrite(e2, max1);
    digitalWrite(m1, HIGH);
    digitalWrite(m2, LOW);
    digitalWrite(m3, HIGH);
    digitalWrite(m4, LOW);
  }
  if ((s1 == 0) && (s2 == 1) && (s3 == 1) && (s4 == 1) && (s5 == 1)) {
    analogWrite(e1, max1);
    analogWrite(e2, min2);
    digitalWrite(m1, HIGH);
    digitalWrite(m2, LOW);
    digitalWrite(m3, HIGH);
    digitalWrite(m4, LOW);
  }
  if ((s1 == 1) && (s2 == 1) && (s3 == 1) && (s4 == 1) && (s5 == 0)) {
    analogWrite(e1, min2);
    analogWrite(e2, max1);
    digitalWrite(m1, HIGH);
    digitalWrite(m2, LOW);
    digitalWrite(m3, HIGH);
    digitalWrite(m4, LOW);
  }
}
