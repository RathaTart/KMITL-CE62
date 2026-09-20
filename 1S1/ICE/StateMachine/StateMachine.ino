#define goN 0
#define waitNtoE 1
#define waitNtoW 2
#define goE 3
#define waitEtoN 4
#define waitEtoW 5
#define goW 6
#define waitWtoN_1 7
#define waitWtoN_2 8
#define waitWtoN_3 9
#define waitWtoN_4 10
#define waitWtoE_1 11
#define waitWtoE_2 12
#define waitWtoE_3 13
#define waitWtoE_4 14


struct State {
unsigned long ST_Out; 
unsigned long Time; 
unsigned long Next[8];
};

State FSM[15] = {
{B10100001, 2000,{0, 0, 1, 1, 2, 2, 1, 1}},     //0
{B10100010, 1000,{3, 3, 3, 3, 3, 3, 3, 3}},     //1
{B10100010, 1000,{6, 6, 6, 6, 6, 6, 6, 6}},     //2
{B10001100, 2000,{3, 4, 3, 4, 5, 5, 5, 5}},     //3
{B10010100, 1000,{0, 0, 0, 0, 0, 0, 0, 0}},     //4
{B10010100, 1000,{6, 6, 6, 6, 6, 6, 6, 6}},     //5
{B01100100, 2000,{6, 7, 11, 7, 6, 7, 11, 7}},   //6
{B00100100, 300, {8, 8, 8, 8, 8, 8, 8, 8}},     //7
{B01100100, 300, {9, 9, 9, 9, 9, 9, 9, 9}},     //8
{B00100100, 300, {10, 10, 10, 10, 10, 10, 10, 10}},   //9 
{B01100100, 300, {0, 0, 0, 0, 0, 0, 0, 0}},           //10
{B00100100, 300, {12, 12, 12, 12, 12, 12, 12, 12}},   //11
{B01100100, 300, {13, 13, 13, 13, 13, 13, 13, 13}},   //12
{B00100100, 300, {14, 14, 14, 14, 14, 14, 14, 14}},   //13
{B01100100, 300, {3, 3, 3, 3, 3, 3, 3, 3}},           //14
};


unsigned long currentState = 0; 
unsigned long long Delay = 0; 

void setup() {
Serial.begin(9600);
for (int i = 2; i <= 9; i++) pinMode(i, OUTPUT);
for (int i = 10; i <= 12; i++) pinMode(i, INPUT_PULLUP);
}
void loop() {
for (int i = 2; i <= 9; i++) {
digitalWrite(i, !(FSM[currentState].ST_Out & 1 << (i - 2)));
}
delay(FSM[currentState].Time);
int input = (1-digitalRead(12)) * 4 + (1-digitalRead(11)) * 2 + (1-digitalRead(10));
currentState = FSM[currentState].Next[input]; 
Serial.write("HUMAN = ");
Serial.println(digitalRead(12));
Serial.write("CAR1 = ");
Serial.println(digitalRead(11));
Serial.write("CAR2 = ");
Serial.println(digitalRead(10));
Serial.write("CURRENT = ");
Serial.println(currentState);
Serial.write("INPUT = ");
Serial.println(input);

}