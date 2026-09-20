#include "ST7735_TEE.h"
#include <time.h>
#include <stdlib.h>

TEE_ST7735 lcd(9, 10, 11, 12, 13);

unsigned long startTime;
// Set the duration of the game in milliseconds (20 seconds)
const unsigned long gameDuration = 10000;
bool gameStarted = false;

const byte PIN_ANALOG_X = 0;
const byte PIN_ANALOG_Y = 1;
const byte PIN_A = 2;
const byte PIN_B = 3;
const byte PIN_C = 4;
const byte PIN_D = 5;
const byte PIN_E = 6;
const byte PIN_F = 7;
const byte PIN_K = 8;

// PLAYER
int pos = 53; 
int prevPos = 53;
int posG = pos + 11;
int prevPosG = pos + 11;
int speed = 2;
int score = 0;
int bullet = 20;
bool shootState = true;
bool game = true;

// ENEMIES
int widthE = 15;
int heigthE = 10;
// enemy 1
int dir1 = 0;
int posEx1 = 0; 
int posEy1 = 50; 
int prevPosEx1 = 0;
int speedE1 = 3;
char textSec[3] = "0", textScore[3] = "0";

void setup() 
{
  Serial.begin(9600);
  srand(time(NULL));

  lcd.init(lcd.VERTICAL); // ปรับให้จอเป็นแนวตั้ง
  lcd.fillScreen(BLACK); // เปลี่ยนสีพื้นหลัง
  lcd.fillRect(pos, 155, 24, 5, BLUE); // ตำแหน่งตัวละคร
  //lcd.fillRect(posG, 140, 2, 15, RED); // ตำแหน่งปืน

  posEx1 = 50 + (rand() % 20);


  pinMode(PIN_A, INPUT);
  digitalWrite(PIN_A, HIGH);
  pinMode(PIN_B, INPUT);
  digitalWrite(PIN_B, HIGH);
  pinMode(PIN_C, INPUT);
  digitalWrite(PIN_C, HIGH);
  pinMode(PIN_D, INPUT);
  digitalWrite(PIN_D, HIGH);
  pinMode(PIN_E, INPUT);
  digitalWrite(PIN_E, HIGH);
  pinMode(PIN_F, INPUT);
  digitalWrite(PIN_F, HIGH);
  pinMode(PIN_K, INPUT);
  digitalWrite(PIN_K, HIGH);

  startTime = millis();
}

void loop() 
{
  while (game == true)
  {
    enemy1();
    
    if (!gameStarted) {
      startTime = millis();
      gameStarted = true;

      // PLAYER
      int pos = 53; 
      int prevPos = 53;
      int posG = pos + 11;
      int prevPosG = pos + 11;
      int speed = 2;
      int score = 0;
      int bullet = 20;
      bool shootState = true;
      bool game = true;

      // ENEMIES
      int widthE = 15;
      int heigthE = 10;
      // enemy 1
      int dir1 = 0;
      int posEx1 = 0; 
      int posEy1 = 50; 
      int prevPosEx1 = 0;
      int speedE1 = 3;
    }

    unsigned long currentTime = millis();
    unsigned long elapsedTime = currentTime - startTime;
    unsigned long remainingTime = max(0, gameDuration - elapsedTime);
    unsigned int seconds = remainingTime / 1000;
    Serial.println(seconds);
    sprintf(textSec, "%d", seconds);
    sprintf(textScore, "%d", score);
    lcd.drawString(50, 10, "TIME = ", WHITE, 1);
    lcd.drawString(100, 10, textSec, WHITE, 1);
    lcd.drawString(50, 20, "SCORE = ", WHITE, 1);
    lcd.drawString(100, 20, textScore, WHITE, 1);
  

    if (analogRead(PIN_ANALOG_X) <= 400 && pos > 5)
    {
      prevPos = pos;
      prevPosG = posG;
      pos -= speed;
      posG -= speed;
      lcd.fillRect(prevPos, 155, 24, 5, BLACK);
      lcd.fillRect(prevPosG, 140, 2, 15, BLACK);
      lcd.fillRect(pos, 155, 24, 5, BLUE);
      //lcd.fillRect(posG, 140, 2, 15, RED);
      
    }

    if (analogRead(PIN_ANALOG_X) >= 600 && pos < 99)
    {
      prevPos = pos;
      prevPosG = posG;
      pos += speed;
      posG += speed;
      lcd.fillRect(prevPos, 155, 24, 5, BLACK);
      lcd.fillRect(prevPosG, 140, 2, 15, BLACK);
      lcd.fillRect(pos, 155, 24, 5, BLUE);
      //lcd.fillRect(posG, 140, 2, 15, RED);
      
    }

    if (digitalRead(PIN_D) == 0 && shootState == true)
    {
      shootState = false;
      shoot();
      lcd.fillRect(0, 0, 4, 160 - 160*bullet/20, BLACK);
      lcd.fillRect(124, 0, 4, 160 - 160*bullet/20, BLACK);
      lcd.fillRect(posG, 0, 2, 155, RED);
      delay(2);
      lcd.fillRect(posG, 0, 2, 155, BLACK);
    }

    if (digitalRead(PIN_D) == 1)
    {
      shootState = true;
    }

    if (elapsedTime >= gameDuration-1000)
    {
      lcd.fillScreen(BLACK);
      lcd.drawString(15, 20, "By 1464 & 1437", WHITE, 1.5);
      lcd.drawString(10, 50, " SCORE:", WHITE, 2);
      lcd.drawString(90, 50, textScore, WHITE, 2);
      lcd.drawString(40, 90, "Wanna Retry!", WHITE, 1);
      lcd.drawString(40, 100, "PRESS B", WHITE, 1);
      game = false;
    }

    delay(5);
    lcd.fillRect(100, 10, 15, 10, BLACK);
    lcd.fillRect(100, 20, 15, 10, BLACK);
  }

  while (game == false)
  {
    if (digitalRead(PIN_B) == 0)
    {
      startTime = millis();
      unsigned long currentTime = millis();
      unsigned long elapsedTime = currentTime - startTime;
      score = 0;
      gameStarted = false;
      bullet = 20;
      pos = 53; 
      prevPos = 53;
      posG = pos + 11;
      prevPosG = pos + 11;
      posEx1 = 50 + (rand() % 20);
      lcd.fillScreen(BLACK);
      lcd.fillRect(pos, 155, 24, 5, BLUE);
    
      game = true;
    }
  }
}

void enemy1()
{
  if (posEx1 <= 25)
  {
    dir1 = 0;
    speedE1 = 5 + (rand() % 5);
  }
  else if (posEx1 >= 100)
  {
    dir1 = 1;
    speedE1 = 5 + (rand() % 5);
  }

  if (dir1 == 0)
  {
    prevPosEx1 = posEx1;
    posEx1 += speedE1;
    lcd.fillCircle(prevPosEx1, posEy1, 7, BLACK);
    lcd.fillCircle(posEx1, posEy1, 7, MAGENTA);
  }
  else if (dir1 == 1)
  {
    prevPosEx1 = posEx1;
    posEx1 -= speedE1;
    lcd.fillCircle(prevPosEx1, posEy1, 7, BLACK);
    lcd.fillCircle(posEx1, posEy1, 7, MAGENTA);
  }
}

void shoot()
{
  if (posG >= posEx1-10 && posG <= posEx1 + 10)
  {
    score++;
  }

  bullet--;
}