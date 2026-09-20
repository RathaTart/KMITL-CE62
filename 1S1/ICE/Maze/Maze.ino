#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include "ST7735_TEE.h"

TEE_ST7735 tft(9, 10, 11, 12, 13);
const byte PIN_ANALOG_X = 0;
const byte PIN_ANALOG_Y = 1;
const byte PIN_A = 2;
const byte PIN_B = 3;
const byte PIN_C = 4;
const byte PIN_D = 5;
const byte PIN_E = 6;
const byte PIN_F = 7;
const byte PIN_K = 8;



bool buttonPressed = false;
int playerX, playerY;
int playerHP = 3;
int startingX = 1; // Set your desired starting X coordinate
int startingY = 1; // Set your desired starting Y coordinate

const int MAZE_WIDTH = 8;
const int MAZE_HEIGHT = 6;
const int CELL_SIZE = 20;
bool maze[MAZE_HEIGHT][MAZE_WIDTH] = {
  {1, 1, 1, 1, 1, 1, 1, 1},
  {1, 0, 0, 0, 1, 0, 0, 1},
  {1, 1, 1, 0, 1, 0, 1, 1},
  {1, 0, 1, 0, 0, 0, 1, 1},
  {1, 0, 1, 1, 1, 0, 0, 1},
  {1, 1, 1, 1, 1, 1, 1, 1},
};

void setup() {
  tft.init(tft.HORIZONTAL);
  //tft.setRotation(3);  // Adjust rotation as needed

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

  // Other setup code for your game logic
  int playerX, playerY;
  // int startingX = 1; // Set your desired starting X coordinate
  // int startingY = 1; // Set your desired starting Y coordinate
  playerX = startingX;
  playerY = startingY;
}

void loop() {
  
  bool buttonStateA = digitalRead(PIN_A);
  bool buttonStateB = digitalRead(PIN_B);
  bool buttonStateC = digitalRead(PIN_C);
  bool buttonStateD = digitalRead(PIN_D);
  bool buttonStateE = digitalRead(PIN_E);
  bool buttonStateF = digitalRead(PIN_F);
  bool buttonStateK = digitalRead(PIN_K);

  // Handle button press
  if ((buttonStateA == LOW || buttonStateB == LOW || buttonStateC == LOW || buttonStateD == LOW || 
       buttonStateE == LOW || buttonStateF == LOW || buttonStateK == LOW) && !buttonPressed) {
    buttonPressed = true;
  } else if (buttonStateA == HIGH && buttonStateB == HIGH && buttonStateC == HIGH && buttonStateD == HIGH && 
             buttonStateE == HIGH && buttonStateF == HIGH && buttonStateK == HIGH) {
    buttonPressed = false;
  }

  int newX = playerX;
  int newY = playerY;

  // Handle player movement based on joystick input
  if (buttonStateA == LOW && !isWall(playerX - 1, playerY)) {
    newX = playerX - 1;  // Move left
  } else if (buttonStateC == LOW && !isWall(playerX + 1, playerY)) {
    newX = playerX + 1;  // Move right
  }
  if (buttonStateB == LOW && !isWall(playerX, playerY - 1)) {
    newY = playerY - 1;  // Move up
  } else if (buttonStateD == LOW && !isWall(playerX, playerY + 1)) {
    newY = playerY + 1;  // Move down
  }

  if (isWall(newX, newY)) {
    // Player collided with a wall, lose HP and return to starting point
    playerHP--;
    if (playerHP <= 0) {
      // Game over, you can add game over logic here
      playerHP = 3;  // Reset HP
    }
    newX = startingX;
    newY = startingY;
  }

  // Update player position
  playerX = newX;
  playerY = newY;

  // Clear the display
  tft.fillScreen(BLACK);

  // Render the maze and player
  for (int row = 0; row < MAZE_HEIGHT; row++) {
    for (int col = 0; col < MAZE_WIDTH; col++) {
      if (maze[row][col]) {
        tft.fillRect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE, WHITE);
      }
    }
  }

  // Render the player's position
  tft.fillCircle(playerX * CELL_SIZE + CELL_SIZE / 2, playerY * CELL_SIZE + CELL_SIZE / 2, 5, RED);

  delay(100);  // Add a delay for smoother movement
}

bool isWall(int x, int y) {
  // Check for wall at the given cell (x, y) in the maze
  if (x < 0 || x >= MAZE_WIDTH || y < 0 || y >= MAZE_HEIGHT) {
    return true;  // Out of bounds
  }
  return maze[y][x];
}
