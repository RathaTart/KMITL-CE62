int PE = 21;      // Connect to the PLAYE pin on the module
int REC = 19;     // Connect to the REC pin on the module
int debugLED = 18; // Optional: Connect an LED to help with debugging

void setup() {
  pinMode(PE, OUTPUT);       // PLAYE control
  pinMode(REC, OUTPUT);      // REC control
  pinMode(debugLED, OUTPUT); // LED for debugging
  Serial.begin(9600);
}

void recordSound() {
  Serial.println("Recording Sound...");
  digitalWrite(REC, HIGH);   // Start recording
  digitalWrite(debugLED, HIGH); // Turn on LED
  delay(2000);               // Record for 2 seconds
  digitalWrite(REC, LOW);    // Stop recording
  digitalWrite(debugLED, LOW);  // Turn off LED
  Serial.println("Recording Complete");
  delay(1000);
}

void playSound() {
  Serial.println("Playing Sound...");
  digitalWrite(PE, HIGH);    // Start playback
  digitalWrite(debugLED, HIGH); // Turn on LED
  delay(100);                // Keep PLAYE pressed
  digitalWrite(PE, LOW);     // Release PLAYE
  digitalWrite(debugLED, LOW);  // Turn off LED
  Serial.println("Playback Complete");
  delay(1000);
}

void loop() {
  recordSound(); // Test recording
  delay(5000);   // Wait for 5 seconds before playback
  playSound();   // Test playback
  delay(10000);  // Wait 10 seconds before repeating the loop
}
