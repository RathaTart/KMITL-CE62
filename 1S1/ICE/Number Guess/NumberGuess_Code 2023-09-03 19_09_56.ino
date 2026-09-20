int bitPattern = B01111111;
const byte numPins = 8;
const int segmentPins[8] = {2,3,4,5,6,7,8,9};
int number[11] = {
  B11000000, //0
  B11111001, //1
  B10100100, //2
  B10110000, //3
  B10011001, //4
  B10010010, //5
  B10000010, //6
  B11111000, //7
  B10000000, //8
  B10010000, //9
  B01111111, //.
};
int HiLo[2] = { B11001110 /*>*/, B11000111 /*<*/}; 
int run = 0;
int input = 0;
long randNumber;

void handle_add_button(){}      

void setup() {
  pinMode(12,INPUT);
  pinMode(13,INPUT);
  Serial.begin(9600);
  for(int i = 0; i < numPins; i++) 
  {
    pinMode(segmentPins[i], OUTPUT);
  }
  //8Serial.println("Please Enter Number = ");
  randomSeed(analogRead(A0));
  randNumber = random(1,10);
  Serial.println(randNumber);
}

void loop() {
  if (digitalRead(12) == HIGH)
  {
    input++;
    //Serial.println("+1");
    if(input == 12) input = 0;
    delay(250);
  }
  if (digitalRead(13) == HIGH)
  {
    if(input < randNumber){
      run = 1;

      bitPattern = HiLo[run];


      boolean isBitSet;
      //Serial.println("Loop");
      for(int segment = 0; segment < numPins; segment++)
      {
        isBitSet = bitRead(bitPattern, segment);
        //Serial.println(isBitSet);
        digitalWrite(segmentPins[segment], isBitSet);
      }
    }
    if(input > randNumber){
      run = 0;

      bitPattern = HiLo[run];


      boolean isBitSet;
      //Serial.println("Loop");
      for(int segment = 0; segment < numPins; segment++)
      {
        isBitSet = bitRead(bitPattern, segment);
        //Serial.println(isBitSet);
        digitalWrite(segmentPins[segment], isBitSet);
      }
    }
    if(input == randNumber) {
      run = 0;

      bitPattern = number[run];


      boolean isBitSet;
      //Serial.println("Loop");
      for(int segment = 0; segment < numPins; segment++)
      {
        isBitSet = bitRead(bitPattern, segment);
        //Serial.println(isBitSet);
        digitalWrite(segmentPins[segment], isBitSet);
      }
      randNumber = random(1,10);
      Serial.println(randNumber);
    }
    input = 11;
    delay(250);
  }
    if((input>=0) && (input<=9))
    {
      run = input;

      bitPattern = number[run];


      boolean isBitSet;
      //Serial.println("Loop");
      for(int segment = 0; segment < numPins; segment++)
      {
        isBitSet = bitRead(bitPattern, segment);
        //Serial.println(isBitSet);
        digitalWrite(segmentPins[segment], isBitSet);
      }
    }
  if (input == 10) input = 0;
}