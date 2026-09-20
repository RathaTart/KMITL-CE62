#include <TridentTD_LineNotify.h>
#include <WiFi.h>

#define SSID        "Tart"                                  // WiFi name
#define PASSWORD    "Tart1347"                                  // WiFi password
#define LINE_TOKEN  "C9z0GWmi4vGw91Z6zswgRLEIRMCLJhf8RIlnkOp4fP9"  // LINE token

int sensor = 23;           // Sensor pin
int led = 22;              // LED pin
int playButton = 13;       // Button to change state
int fpgaSignal = 25;       // D34 to send state change signal to FPGA
int i = 0;                 // Coin count
int c = 0;                 // Amount in currency
int credit = 0;          // Credits to play
int state = 0;             // Slot machine state
volatile bool playing = false;
volatile bool isCounter = false;
volatile int count = 0;
unsigned long lastInterruptTime = 0; // For debouncing

// Define pins for 7-bit output
int outputPins[7] = {21, 19, 18, 5, 4, 2, 15}; // D21 (LSB), D15 (MSB)

// Define pins for 4-bit input from FPGA
int fpgaInputPins[4] = {12, 14, 17, 33}; // D12 (LSB), D33 (MSB)

void IRAM_ATTR doCounter() {
  unsigned long interruptTime = millis();
  if (interruptTime - lastInterruptTime > 200) {
    isCounter = true;
    count++;
    lastInterruptTime = interruptTime;
  }
}

void setup() {
  Serial.begin(115200); 
  Serial.println();
  Serial.println(LINE.getVersion());

  // Connect to WiFi
  WiFi.begin(SSID, PASSWORD);
  Serial.printf("WiFi connecting to %s\n", SSID);
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(400);
  }
  Serial.printf("\nWiFi connected\nIP : ");
  Serial.println(WiFi.localIP());

  // Set LINE token
  LINE.setToken(LINE_TOKEN);

  // Pin setup
  pinMode(sensor, INPUT);
  pinMode(led, OUTPUT);
  pinMode(playButton, INPUT);      // Button to change state
  pinMode(fpgaSignal, OUTPUT);     // D34 to send signal to FPGA
  attachInterrupt(digitalPinToInterrupt(sensor), doCounter, RISING);

  // Initialize 7-bit output pins
  for (int j = 0; j < 7; j++) {
    pinMode(outputPins[j], OUTPUT);
  }

  // Initialize FPGA input pins
  for (int j = 0; j < 4; j++) {
    pinMode(fpgaInputPins[j], INPUT);
  }

  // Send initial notification
  LINE.notify("Coin Collector Machine Ready!");
}

void updateOutputPins(int value) {
  for (int j = 0; j < 7; j++) {
    digitalWrite(outputPins[j], (value >> j) & 0x01);
  }
}

void sendStateSignal() {
  // Send a state change signal on D34
  digitalWrite(fpgaSignal, HIGH);
  delay(100);  // Signal duration
  digitalWrite(fpgaSignal, LOW);
}

void readBinaryInput() {
  unsigned long startTime = millis(); // Record the start time
  bool shouldPrint = false;

  int bit0 = digitalRead(fpgaInputPins[0]); // LSB (D12)
  int bit1 = digitalRead(fpgaInputPins[1]); // D14
  int bit2 = digitalRead(fpgaInputPins[2]); // D17
  int bit3 = digitalRead(fpgaInputPins[3]); // MSB (D33)

  // Interpret the 4-bit binary input as a single integer
  int fpgaInput = (bit3 << 3) | (bit2 << 2) | (bit1 << 1) | bit0;

  // Check for specific binary values
  if (fpgaInput == 0b1000) { // 1000 in binary
    LINE.notify("You won LLL, 10 points");
  } else if (fpgaInput == 0b0100) { // 0100 in binary
    LINE.notify("You won 777, 100 points"); 
  } else if (fpgaInput == 0b0010) { // 0010 in binary
    LINE.notify("You won 888, 50 points");
  } else if (fpgaInput == 0b0001) { // 0001 in binary
    LINE.notify("You won CCC, 20 points");
  }

  // Determine if any bit is 1
  if (bit0 || bit1 || bit2 || bit3) {
    shouldPrint = true;
  }

  // Print the binary value if any bit is not zero, for 2 seconds
  if (shouldPrint) {
    while (millis() - startTime < 2000) {  // Continue for 2 seconds
      Serial.print("Received 4-bit binary value: ");
      Serial.print(bit3);  // MSB
      Serial.print(bit2);
      Serial.print(bit1);
      Serial.println(bit0); // LSB
      delay(500);  // Adjust delay as needed for frequency of printing
    }
  }
}

void startSlotMachine() {
  Serial.print("Current State: ");
  Serial.println(state);

  switch (state) {
    case 0:  // Initial state: xxx
      Serial.println("Slot Machine: xxx");
      sendStateSignal();  // Send signal to move to next state
      state = 1;
      break;
    case 1:  // Random number run 3xx
      Serial.println("Slot Machine: Randomizing 3xx");
      sendStateSignal();
      state = 2;
      break;
    case 2:  // Display xx1
      Serial.println("Slot Machine: xx1");
      sendStateSignal();
      state = 3;
      break;
    case 3:  // Display x21
      Serial.println("Slot Machine: x21");
      sendStateSignal();
      state = 4;
      break;
    case 4:  // Display 321 and reset to initial state
      Serial.println("Slot Machine: 321");
      sendStateSignal();
      state = 0;
      credit -= 1;   // Deduct one credit
      c -= 10;       // Deduct 10 baht from total currency
      updateOutputPins(c);  // Update display to show new amount
      Serial.print("Remaining Credit: ");
      Serial.println(credit);
      Serial.print("Remaining Money: ");
      Serial.println(c);
      if (c < 0) c = 0;  // Ensure currency doesn't go negative

      String message = "เล่นเสร็จ\nจำนวนเงินที่เหลือ: " + String(c) + " บาท | จำนวนเครดิตที่เหลือ: " + String(credit);
      LINE.notify(message);
      break;
  }
}

void loop() {
  if (isCounter) {
    isCounter = false;
    if (count > 0) {
      i++;  // Increment coin count
      c += 10;  // Add 10 baht to total currency amount
      credit = c / 10;  // Calculate credits based on total amount

      Serial.print("Coin Count: ");
      Serial.println(i);
      Serial.print("Total Money: ");
      Serial.println(c);
      Serial.print("Current Credit: ");
      Serial.println(credit);

      digitalWrite(led, HIGH);
      delay(50);
      digitalWrite(led, LOW);

      count = 0;


      String message = "จำนวนเหรียญ: " + String(i) + " | จำนวนเงิน: " + String(c) + " บาท | จำนวนเครดิต: " + String(credit);
      LINE.notify(message);

      updateOutputPins(c);  // Send the amount as binary to FPGA
    }
  }

  bool buttonPressed = (digitalRead(playButton) == LOW);
  Serial.print("Play Button Status: ");
  Serial.println(buttonPressed ? "Pressed" : "Not Pressed");
  delay(50);

  if (buttonPressed && credit > 0) {
    delay(10); // Debounce delay
    while (digitalRead(playButton) == LOW); // Wait for button release
    startSlotMachine();       // Progress through slot machine states
    readBinaryInput();        // Read and display binary input from FPGA
  }
}