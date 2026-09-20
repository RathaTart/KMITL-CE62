#define port_vcc_1 12
#define port_vcc_2 11
#define port_vcc_3 10
#define port_gnd_1 7
#define port_gnd_2 6
#define port_gnd_3 5

void setup() {
  pinMode(port_vcc_1, OUTPUT);
  pinMode(port_vcc_2, OUTPUT);
  pinMode(port_vcc_3, OUTPUT);
  pinMode(port_gnd_1, OUTPUT);
  pinMode(port_gnd_2, OUTPUT);
  pinMode(port_gnd_3, OUTPUT);


}

void loop() {
  
  //Write 1 for 1 sec
  for(int i=0; i<250; i++)
  {
    digitalWrite(port_vcc_1, HIGH);
    digitalWrite(port_vcc_2, LOW);
    digitalWrite(port_vcc_3, HIGH);
    digitalWrite(port_gnd_1, LOW);
    digitalWrite(port_gnd_2, LOW);
    digitalWrite(port_gnd_3, LOW);
    
    delay(1);
    
    digitalWrite(port_vcc_1, HIGH);
    digitalWrite(port_vcc_2, HIGH);
    digitalWrite(port_vcc_3, HIGH);
    digitalWrite(port_gnd_1, LOW);
    digitalWrite(port_gnd_2, HIGH);
    digitalWrite(port_gnd_3, LOW);
    
    delay(1);
  }

  //Write X for 1 sec
  for(int i=0; i<200; i++)
  {
    digitalWrite(port_vcc_1, HIGH);
    digitalWrite(port_vcc_2, LOW);
    digitalWrite(port_vcc_3, LOW);
    digitalWrite(port_gnd_1, LOW);
    digitalWrite(port_gnd_2, HIGH);
    digitalWrite(port_gnd_3, HIGH);
    
    delay(1);
    
    digitalWrite(port_vcc_1, LOW);
    digitalWrite(port_vcc_2, LOW);
    digitalWrite(port_vcc_3, HIGH);
    digitalWrite(port_gnd_1, HIGH);
    digitalWrite(port_gnd_2, HIGH);
    digitalWrite(port_gnd_3, LOW);
    
    delay(1);
    
    digitalWrite(port_vcc_1, LOW);
    digitalWrite(port_vcc_2, LOW);
    digitalWrite(port_vcc_3, HIGH);
    digitalWrite(port_gnd_1, LOW);
    digitalWrite(port_gnd_2, HIGH);
    digitalWrite(port_gnd_3, HIGH);
    
    delay(1);

    digitalWrite(port_vcc_1, HIGH);
    digitalWrite(port_vcc_2, LOW);
    digitalWrite(port_vcc_3, LOW);
    digitalWrite(port_gnd_1, HIGH);
    digitalWrite(port_gnd_2, HIGH);
    digitalWrite(port_gnd_3, LOW);
    
    delay(1);

    digitalWrite(port_vcc_1, LOW);
    digitalWrite(port_vcc_2, HIGH);
    digitalWrite(port_vcc_3, LOW);
    digitalWrite(port_gnd_1, HIGH);
    digitalWrite(port_gnd_2, LOW);
    digitalWrite(port_gnd_3, HIGH);
    
    delay(1);
  }



}
