#include "LedControl.h"
#include "binary.h"

/*
 DIN connects to pin 11
 CLK connects to pin 13
 CS connects to pin 10 
*/
LedControl lc=LedControl(11,13,10,1);

// delay time between dot
unsigned long delaytime=100;

// happy face
byte dot[8]= { B10000000 , B01000000, B00100000, B00010000, B00001000, B00000100, B0000010, B00000001};

void setup() {
  lc.shutdown(0,false);
  // Set brightness to a medium value
  lc.setIntensity(0,8);
  // Clear the display
  lc.clearDisplay(0);  
}

void drawSquare(){
  // Display sad face

  for(int i=0; i<8; i++)
  {
    lc.setRow(0,i,dot[0]);
    delay(delaytime);
    lc.clearDisplay(0);  
  }
  for(int i=0; i<8; i++)
  {
    lc.setRow(0,7,dot[i]);
    delay(delaytime);
    lc.clearDisplay(0);  
  }
  for(int i=7; i>=0; i--)
  {
    lc.setRow(0,i,dot[7]);
    delay(delaytime);
    lc.clearDisplay(0);  
  }
  for(int i=7; i>=0; i--)
  {
    lc.setRow(0,0,dot[i]);
    delay(delaytime);
    lc.clearDisplay(0);  
  }
}

void loop(){
  drawSquare();
}