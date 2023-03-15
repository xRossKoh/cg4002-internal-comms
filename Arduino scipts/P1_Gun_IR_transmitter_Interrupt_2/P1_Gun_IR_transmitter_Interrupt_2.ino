// ================================================================
// ===               INTERNAL COMMS CODE              ===
// ================================================================
#pragma pack(1)
// ================================================================
// ===               LIBRARIES + VARIABLES              ===
// ================================================================
#include <Arduino.h>
#include <TinyIRSender.hpp>

#define PUSHBUTTON_PIN  2
#define IR_SEND_PIN         3

byte segPins[] = {A3, A4, 4, 5, A5, A2, A1}; //7-seg LED segment display

//CHANGEABLE VARIABLE:
int ammo = 6; //6 bullets at start of game

#define switched                            true // value if the button switch has been pressed
#define triggered                           true // controls   interrupt handler
#define interrupt_trigger_type            RISING // interrupt   triggered on a RISING input
#define debounce                              10000   // time to wait in milli secs
volatile  bool interrupt_process_status = {
  !triggered                                     // start with no switch press pending,   ie false (!triggered)
};
bool initialisation_complete =            true;   // inhibit any interrupts until initialisation is complete

uint16_t sAddress = 0x0102;
// ================================================================
// ===               INTERNAL COMMS CODE              ===
// ================================================================

/*---------------- Data structures ----------------*/

enum PacketType
{
  HELLO,
  ACK,
  NACK,
  DATA
};

typedef struct
{
  uint8_t header;           // 1 byte header: 4 bit node id | 2 bit packet type | 2 bit sequence no
  uint8_t padding;          // padding header to 2 bytes
  int euler_x;              // contains IR data for data packet for IR sensors
  int euler_y;              // all other fields padded with 0 for data packet for IR sensors
  int euler_z;
  int acc_x;
  int acc_y;
  int acc_z;
  int flex_1;
  int flex_2;
  uint16_t crc;             // Cyclic redundancy check (CRC-16)
} BLEPacket;

/*---------------- Global variables ----------------*/

const unsigned int PACKET_SIZE = 20;
const unsigned int PKT_THRESHOLD = 5;
const int default_data[] = {0, 0, 0, 0, 0, 0, 0, 0};
const int shoot_data[] = {1, 0, 0, 0, 0, 0, 0, 0};

static unsigned int bullets = 6;
static unsigned int numShots = 0;
static unsigned int seqNo = 1;
static unsigned int counter = 0;

uint8_t serial_buffer[PACKET_SIZE];
BLEPacket* curr_packet;

/*---------------- CRC calculation ----------------*/

uint16_t crcCalc(uint8_t* data)
{
   uint16_t curr_crc = 0x0000;
   uint8_t sum1 = (uint8_t) curr_crc;
   uint8_t sum2 = (uint8_t) (curr_crc >> 8);

   for (int i = 0; i < PACKET_SIZE; i++)
   {
      sum1 = (sum1 + data[i]) % 255;
      sum2 = (sum2 + sum1) % 255;
   }
   return (sum2 << 8) | sum1;
}

/*---------------- Checks ----------------*/

bool crcCheck()
{
  uint16_t crc = curr_packet->crc;
  curr_packet->crc = 0;
  return (crc == crcCalc((uint8_t*)curr_packet));
}

bool packetCheck(uint8_t node_id, PacketType packet_type)
{
  uint8_t header = curr_packet->header;
  uint8_t curr_node_id = (header & 0xf0) >> 4;
  PacketType curr_packet_type = PacketType((header & 0b1100) >> 2);
  return curr_node_id == node_id && curr_packet_type == packet_type;
}

bool seqNoCheck()
{
  uint8_t header = curr_packet->header;
  uint8_t curr_seq_no = header & 0b1;
  return curr_seq_no != seqNo;
}

/*---------------- Packet management ----------------*/


BLEPacket generatePacket(PacketType packet_type, int* data)
{
  BLEPacket p;
  p.header = (1 << 4) | (packet_type << 2) | seqNo;
  p.padding = 0;
  p.euler_x = data[0];
  p.euler_y = data[1];
  p.euler_z = data[2];
  p.acc_x = data[3];
  p.acc_y = data[4];
  p.acc_z = data[5];
  p.flex_1 = data[6];
  p.flex_2 = data[7];
  p.crc = 0;
  uint16_t calculatedCRC = crcCalc((uint8_t*)&p);
  p.crc = calculatedCRC;
  return p;
}

void sendPacket(PacketType packet_type, int* data)
{
  BLEPacket p = generatePacket(packet_type, data);
  Serial.write((byte*)&p, PACKET_SIZE);
}

void sendDefaultPacket(PacketType packet_type)
{
  sendPacket(packet_type, default_data);
}

void sendDataPacket()
{
  int data[] = {counter, 0, 0, 0, 0, 0, 0, 0};
  sendPacket(DATA, data);
}

/*---------------- Game state handler ----------------*/

void updateGameState()
{
  bullets = curr_packet->euler_x;
}

/*---------------- Communication protocol ----------------*/

void waitForData()
{
  unsigned int buf_pos = 0;
  while (buf_pos < PACKET_SIZE)
  {
    if (Serial.available())
    {
      uint8_t in_data = Serial.read();
      serial_buffer[buf_pos] = in_data;
      buf_pos++;
    }
  }
  curr_packet = (BLEPacket*)serial_buffer;
}

void threeWayHandshake()
{
  bool is_connected = false;
  while (!is_connected)
  {
    // wait for hello from laptop
    waitForData();
  
    if (!crcCheck() || !packetCheck(0, HELLO))
    {
      sendDefaultPacket(NACK);
      continue;
    } 
    sendDefaultPacket(HELLO);

    // reset seq no
    seqNo = 1;

    numShots = 0;
    
    // wait for ack from laptop
    waitForData();
    
    if (crcCheck() && packetCheck(0, ACK))
    {
      updateGameState();
      is_connected = true;
    }
  }
}

// ================================================================
// ===               BUTTON INTERRUPT FUNCTIONS              ===
// ================================================================
bool read_button() {
  int button_reading;
  // static variables because we need to retain old values between function calls
  static bool switching_pending = false;
  static long int elapse_timer;
  if (interrupt_process_status == triggered) {
    //  interrupt has been raised on this button so now need to complete
    // the button  read process, ie wait until it has been released
    // and debounce time elapsed
    button_reading = digitalRead(PUSHBUTTON_PIN);
    if (button_reading == HIGH)   {
      // switch is pressed, so start/restart wait for button relealse, plus   end of debounce process
      switching_pending = true;
      elapse_timer   = micros(); // start elapse timing for debounce checking
    }
    if (switching_pending  && button_reading == LOW) {
      // switch was pressed, now released, so check   if debounce time elapsed
      if (micros() - elapse_timer >= debounce) {
        // dounce time elapsed, so switch press cycle complete
        switching_pending   = false;             // reset for next button press interrupt cycle
        return switched;                       // advise that switch has been pressed
      }
    }
  }
  return !switched; // either no press request or debounce period not elapsed
}

volatile int num_Shots  = 0;
void   button_interrupt_handler()
{
  if (initialisation_complete == true)
  { //  all variables are initialised so we are okay to continue to process this interrupt
    if (interrupt_process_status == !triggered) {
      if (digitalRead(PUSHBUTTON_PIN) == HIGH) {
        // button   pressed, so we can start the read on/off + debounce cycle wich will be completed by the button_read() function.
        interrupt_process_status   = triggered;  // keep this ISR 'quiet' until button read fully completed
        noInterrupts();
        while (read_button() != true){}; //EXIT LOOP - ie. button is pressed & released
        num_Shots++;
        Serial.println("shot");
        //reenable interrupt:
        interrupt_process_status   = !triggered;
        interrupts();
      }
    }
  }
}

// ================================================================
// ===               SETUP CODE              ===
// ================================================================
void setup() {
  
  Serial.begin(115200);
  
  //enable button:
  pinMode(PUSHBUTTON_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(PUSHBUTTON_PIN), button_interrupt_handler, interrupt_trigger_type);
                  
  //enable IR LED:
  pinMode(IR_SEND_PIN, OUTPUT);  
  
  //enable LED 7 seg display:
  pinMode(13,OUTPUT);
  for(int i =0; i< 7; i++) {
    pinMode(segPins[i], OUTPUT);
  }
  
  //initialise led seg display to display 6 bullets:
  sevsegSetNumber(6);

  // int comms set up
  threeWayHandshake();
}


// ================================================================
// ===               FUNCTIONS            ===
// ================================================================
void display_0(){
      digitalWrite(segPins[0], LOW);
      digitalWrite(segPins[1], LOW);
      digitalWrite(segPins[2], LOW);
      digitalWrite(segPins[3], LOW);  
      digitalWrite(segPins[4], LOW);
      digitalWrite(segPins[5], LOW);      
      digitalWrite(segPins[6], HIGH);   
}
void display_1(){
      digitalWrite(segPins[1], LOW);
      digitalWrite(segPins[2], LOW);
      digitalWrite(segPins[0], HIGH);
      digitalWrite(segPins[3], HIGH);  
      digitalWrite(segPins[4], HIGH);
      digitalWrite(segPins[5], HIGH);      
      digitalWrite(segPins[6], HIGH);   
}
void display_2(){
      digitalWrite(segPins[2], HIGH);
      digitalWrite(segPins[5], HIGH);
      digitalWrite(segPins[0], LOW);
      digitalWrite(segPins[1], LOW);  
      digitalWrite(segPins[3], LOW);
      digitalWrite(segPins[4], LOW);      
      digitalWrite(segPins[6], LOW);  
}
void display_3(){
      digitalWrite(segPins[5], HIGH);
      digitalWrite(segPins[4], HIGH);
      digitalWrite(segPins[1], LOW);
      digitalWrite(segPins[0], LOW);
      digitalWrite(segPins[2], LOW);
      digitalWrite(segPins[3], LOW);  
      digitalWrite(segPins[6], LOW);
}
void display_4(){
      digitalWrite(segPins[0], HIGH);
      digitalWrite(segPins[4], HIGH);
      digitalWrite(segPins[3], HIGH);
      digitalWrite(segPins[1], LOW);  
      digitalWrite(segPins[2], LOW);
      digitalWrite(segPins[5], LOW);      
      digitalWrite(segPins[6], LOW);    
}
void display_5(){
      digitalWrite(segPins[1], HIGH);
      digitalWrite(segPins[4], HIGH);
      digitalWrite(segPins[0], LOW);
      digitalWrite(segPins[2], LOW);  
      digitalWrite(segPins[3], LOW);
      digitalWrite(segPins[5], LOW);      
      digitalWrite(segPins[6], LOW);        
}
void display_6(){
      digitalWrite(segPins[1], HIGH);
      digitalWrite(segPins[0], LOW);
      digitalWrite(segPins[2], LOW);
      digitalWrite(segPins[3], LOW);  
      digitalWrite(segPins[4], LOW);
      digitalWrite(segPins[5], LOW);      
      digitalWrite(segPins[6], LOW);   
}
void sevsegSetNumber(int num){
  if (num == 0) {
    display_0();
  }
  if (num == 1) {
    display_1();
  }
  if (num == 2) {
    display_2();
  }
  if (num == 3){
    display_3();
  }
  if (num == 4){
    display_4();
  }
  if (num == 5){
    display_5();
  }
  if (num == 6){
    display_6();
  }
}

int stored_Num_Shots = 0;
////This function sends data pkt to relay node till ack:
//void send_data_pkt(){
//    data[0] = stored_Num_Shots;
//    bool is_ack = false;
//    while (!is_ack) // packet will keep sending until it is acknowledged by laptop
//    {
//      sendDataPacket(data);
//      waitForData();
//      if (!crcCheck()) continue;
//      if (packetCheck(0, ACK))
//      {
//        is_ack = true;
//      }
//      else if (packetCheck(0, HELLO))
//      {
//        sendDefaultPacket(HELLO);
//      
//        // wait for ack from laptop
//        waitForData();
//  
//        if (crcCheck() && packetCheck(0, ACK))
//        {
//          is_ack = true;
//        }
//      }
//    }
//}

void toggle_Ammo_display(){
    if(ammo > 0) {
      ammo -= stored_Num_Shots; //minus one for ammo and display this number on led segment display + send this info to visualiser
    }
    //ammo = 0; if user reload, reset ammo to 6
    else {
      ammo = 6;
    } 
    sevsegSetNumber(ammo);
}

// ================================================================
// ===               MAIN LOOP              ===
// ================================================================
void loop() {
  delay(100);
  if (numShots > 0)
  {
    // increment sequence number for next packet
    seqNo++;
    seqNo %= 2;

    // initialize loop variables
    unsigned int pkt_count = 0;
    bool is_ack = false;

    while (!is_ack)
    {
      // only send data packet if the number of received ACKs has exceeded threshold
      if (pkt_count == 0) sendDataPacket();

      // receive and buffer serial data
      waitForData();

      // increment packet count
      pkt_count++;
      pkt_count %= PKT_THRESHOLD;
      
      // do checks on received data
      if (!crcCheck()) continue;
      if (packetCheck(0, ACK) && seqNoCheck())
      {
        numShots--;
        counter++;
        updateGameState();
        is_ack = true;
      }
      else if (packetCheck(0, HELLO)) // reinitiate 3-way handshake
      {
        sendDefaultPacket(HELLO);

        // reset seq no
        seqNo = 1;

        numShots = 0;
        
        // wait for ack from laptop
        waitForData();
        
        if (crcCheck() && packetCheck(0, ACK))
        {
          updateGameState();
          is_ack = true;
        }
      }
    }
  }
  else
  {
    waitForData();
    if (!crcCheck()) return;
    if (packetCheck(0, HELLO)) // reinitiate 3-way handshake
    {
      sendDefaultPacket(HELLO);

      // reset seq no
      seqNo = 1;

      numShots = 0;
      
      // wait for ack from laptop
      waitForData();
      
      if (crcCheck() && packetCheck(0, ACK))
      {
        updateGameState();
      }
    }
    else if (packetCheck(0, ACK) && seqNoCheck()) // game state broadcast
    {
      updateGameState();
    }
  }
//  // ===               DATA PACKET              ===
//  for (int i = 0; i < 8; i++)
//  {
//    data[i] = 0; 
//  }
//  
//  // ===               MAIN CODE              ===
//      
//  //while there are pending shots to be processed, send IR LED to opponent, toggle Ammo display & send data pkt to relay node
//  if (num_Shots > 0) {
//    int stored_Num_Shots = num_Shots;
//    num_Shots -= stored_Num_Shots;
//    for (int i  = 0; i < stored_Num_Shots; i++) {
//          sendNECMinimal(IR_SEND_PIN, 0, 2 ,0); //Send IR LED -> Command sent: 0x02 //P1 sents '2' to P2
//    }
//    //IrSender.sendNEC(sAddress, 0x02, 0); //Send IR LED -> Command sent: 0x02
//    toggle_Ammo_display(); //Change ammo count displayed on 7-seg LED
//    
//    // ===               DATA PACKET              ===
//    send_data_pkt(); //Send pkt to relay node
//  }

  // ===               END              ===
}
