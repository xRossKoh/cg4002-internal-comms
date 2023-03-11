#pragma pack(1)

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
  uint8_t header;           // contains beetle id and packet type
  uint8_t padding;          // Padding header to 2 bytes
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

static unsigned int health = 100;
static unsigned int numHits = 0;

uint8_t serial_buffer[PACKET_SIZE];
BLEPacket* curr_packet;

BLEPacket default_packets[4];

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
  PacketType curr_packet_type = PacketType(header & 0xf);
  return curr_node_id == node_id && curr_packet_type == packet_type;
}

/*---------------- Packet management ----------------*/


BLEPacket generatePacket(PacketType packet_type, int* data)
{
  BLEPacket p;
  p.header = (1 << 4) | packet_type;
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

void generateDefaultPackets()
{
  int data[] = {0, 0, 0, 0, 0, 0, 0, 0};
  for (int i = 0; i < 4; i++)
  {
    if (i == 3) data[0] = 1;
    default_packets[i] = generatePacket(PacketType(i), data);
  }
}

void sendDefaultPacket(PacketType packet_type)
{
  Serial.write((byte*)&default_packets[packet_type], PACKET_SIZE);
}

//void sendDataPacket(int* data)
//{
//  BLEPacket p = generatePacket(DATA, data);
//  Serial.write((byte*)&p, PACKET_SIZE);
//}

/*---------------- Game state handler ----------------*/

void updateGameState()
{
  health = curr_packet->euler_y;
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
    
    // wait for ack from laptop
    waitForData();
    
    if (crcCheck() && packetCheck(0, ACK))
    {
      is_connected = true;
    }
  }
}

/*---------------- Setup ----------------*/

void setup() {
  Serial.begin(115200);
  generateDefaultPackets();
  threeWayHandshake();
}

/*---------------- Main ----------------*/

void loop() {
  if (Serial.available())
  {
    waitForData();
    if (!crcCheck()) return;
    if (packetCheck(0, HELLO))
    {
      sendDefaultPacket(HELLO);
  
      // wait for ack from laptop
      waitForData();

      if (crcCheck() && packetCheck(0, ACK))
      {
        updateGameState();
      }
    }
    else if (packetCheck(0, ACK))
    {
      updateGameState();
      sendDefaultPacket(ACK);
    }
  }

  if (numHits > 0)
  {
    bool is_ack = false;
    while (!is_ack)
    {
      sendDefaultPacket(DATA);
      waitForData();
      if (!crcCheck()) continue;
      if (packetCheck(0, ACK))
      {
        updateGameState();
        is_ack = true;
        numHits--;
      }
      else if (packetCheck(0, HELLO))
      {
        sendDefaultPacket(HELLO);
      
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
}
