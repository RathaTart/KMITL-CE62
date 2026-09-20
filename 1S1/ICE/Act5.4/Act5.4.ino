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
int run = 0;
int input = 0;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  for(int i = 0; i < numPins; i++) 
  {
    pinMode(segmentPins[i], OUTPUT);
  }
  Serial.println("Please Enter Number = ");

}

void loop() {
  // put your main code here, to run repeatedly:
  // Serial.println("Please Enter Number = ");
  // while ()
  if (Serial.available() > 0) 
  {
    
    input = Serial.read()-'0';
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
      Serial.println("Please Enter Number = ");
    }
    else if(input  > -38)
    {
      boolean isBitSet;
      Serial.println("ERROR");
      for(int segment = 0; segment < numPins; segment++)
      {
        
        isBitSet = bitRead(B01111111, segment);
        //Serial.println(isBitSet);
        digitalWrite(segmentPins[segment], isBitSet);
        //Serial.println("INSIDE");
      }
      Serial.println("Please Enter Number = ");
    }
  }
}