#pragma pack(1)

#include <Wire.h>
const int MPU = 0X68;

float AccX, AccY, AccZ;
int ax, ay, az = 0; //AccX, Y, z converted to int type
float GyroX, GyroY, GyroZ;
int gx, gy, gz = 0; //GyroX,Y,Z converted to int type

float AccErrorX, AccErrorY, AccErrorZ, GyroErrorX, GyroErrorY, GyroErrorZ = 0;
float elapsedTime, currentTime, previousTime = 0;
int c = 0;

static float AccXSum = 0;
static float AccYSum = 0;
static float AccZSum = 0;
static float GyroXSum = 0;
static float GyroYSum = 0;
static float GyroZSum = 0;
static float middleAngleSum = 0;
static float lastAngleSum = 0;

static int count = 0;

/*---------------- Constants --------------------*/

const int lastFinger = A2;      // Pin connected to voltage divider output
const int middleFinger = A3;      // Pin connected to voltage divider output
int middleFlex, lastFlex = 0;

// Change these constants according to your project's design
const float VCC = 5;      // voltage at Ardunio 5V line
const float R_DIV = 10000.0;  // resistor used to create a voltage divider

const float middleFlatResistance = 10920.05;// resistance when flat
const float middleBendResistance = 21968.75;  // resistance at 90 deg
//P2: 
//flat - 10920.05
//90 - 21968.75
//open - 10217.39
//closed- 26021.13

const float lastFlatResistance = 33164.56;// resistance when flat
const float lastBendResistance = 59591.84;  // resistance at 90 deg
//p2:
//opem - 30756.97
//closed - 56000.00
//flat - 33164.56
// 90 - 59591.84

enum PacketType
{
  HELLO,
  ACK,
  NACK,
  DATA
};

typedef struct
{
  uint8_t header;           // 1 byte: contains 4 bits beetle id, 2 bit packet type, 2 bit seq no
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

const unsigned int PACKET_SIZE = 20;

uint8_t serial_buffer[PACKET_SIZE];
BLEPacket* curr_packet;

bool is_connected = false;

BLEPacket default_packets[3];

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

BLEPacket generatePacket(PacketType packet_type, int* data)
{
  BLEPacket p;
  p.header = (3 << 4) | (packet_type << 2) | 0;
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
  for (int i = 0; i < 3; i++)
  {
    default_packets[i] = generatePacket(PacketType(i), data);
  }
}

void sendDefaultPacket(PacketType packet_type)
{
  Serial.write((byte*)&default_packets[packet_type], PACKET_SIZE);
}

void sendDataPacket(int* data)
{
  BLEPacket p = generatePacket(DATA, data);
  Serial.write((byte*)&p, PACKET_SIZE);
}

void threeWayHandshake()
{
//  bool is_connected = false;
  while (!is_connected)
  {
    // wait for hello from laptop
    waitForData();
  
    if (!crcCheck() or !packetCheck(0, HELLO))
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

void setup() {
  
  Serial.begin(115200);

  //Initialise wire library:
  Wire.begin();

  //Reset the sensor through the Power Management Register:
  Wire.beginTransmission(MPU);
  Wire.write(0x6B); //Talk to Register 6B
  Wire.write(0x00);  //Reset sensor - place a 0 into 6B register
  Wire.endTransmission(true); //end Transmission

  //Configure Accelerometer sensitivity - Full Scale Range(+/-2g)
  Wire.beginTransmission(MPU);
  Wire.write(0x1C);
  Wire.write(0x00); //Set register bits as 00010000 (+/- 2g full scale range)
  Wire.endTransmission(true);

  //Configure Gyro Sensitivity - Full Scale Range(default +/-250 deg/s)
  Wire.beginTransmission(MPU);
  Wire.write(0x1B);
  Wire.write(0x00);
  Wire.endTransmission(true);

  //Configure DLPF - Digital Low-Pass Filter to 5Hz
  Wire.beginTransmission(MPU);
  Wire.write(0x1A);
  Wire.write(0x06);
  Wire.endTransmission(true);
  
  //calc_IMU_error();
  generateDefaultPackets();
  threeWayHandshake();
}

//This function calculates IMU acc and gyro error - IMU is placed flat
void calc_IMU_error(){
  
  while (c < 10000) {
    Wire.beginTransmission(MPU);
    Wire.write(0x3B);
    Wire.endTransmission(false);
    Wire.requestFrom(MPU, 6, true);

    AccX = (Wire.read() << 8 | Wire.read()) / 16384.0;
    AccY = (Wire.read() << 8 | Wire.read()) / 16384.0;
    AccZ = (Wire.read() << 8 | Wire.read()) / 16384.0;

    //Sum all readings:
    AccErrorX = AccErrorX + AccX;
    AccErrorY = AccErrorY + AccY;
    AccErrorZ = AccErrorZ + AccZ;
    c++;
  }
  //Divide sum by 200 to get error value:
  AccErrorX = AccErrorX / 10000;
  AccErrorY = AccErrorY / 10000;
  AccErrorZ = AccErrorZ / 10000;

  c = 0;
  //Read Gyro 200 times:
  while (c < 200) {
    Wire.beginTransmission(MPU);
    Wire.write(0x43);
    Wire.endTransmission(false);
    Wire.requestFrom(MPU, 6, true);

    GyroX = (Wire.read() << 8 | Wire.read()) / 131.0;
    GyroY = (Wire.read() << 8 | Wire.read()) / 131.0;
    GyroZ = (Wire.read() << 8 | Wire.read()) / 131.0;

    //Sum all readings:
    GyroErrorX = GyroErrorX + GyroX;
    GyroErrorY = GyroErrorY + GyroY;
    GyroErrorZ = GyroErrorZ + GyroZ;
    c++;
  }

  //Divide by 200 to get Gyro error:
  GyroErrorX = GyroErrorX / 10000;
  GyroErrorY = GyroErrorY / 10000;
  GyroErrorZ = GyroErrorZ / 10000;

  Serial.print(AccErrorX);
  Serial.print(" ");
  Serial.print(AccErrorY);
  Serial.print(" ");
  Serial.print(AccErrorZ);
  Serial.print(" ");
  
  Serial.print(GyroErrorX);
  Serial.print(" ");
  Serial.print(GyroErrorY);
  Serial.print(" ");
  Serial.println(GyroErrorZ);
  
} 

// Function to swap two integers
void swap(float *x, float *y) {
    int temp = *x;
    *x = *y;
    *y = temp;
}

// Function to calculate the median of an array
double median(float arr[]) {
    // Sort the array using bubble sort
    for (int i = 0; i < 5; i++) {
        for (int j = 0; j < 5 - i; j++) {
            if (arr[j] > arr[j + 1]) {
                swap(&arr[j], &arr[j + 1]);
            }
        }
    }

    // Calculate the median
    return (double)arr[2];
}

void loop() {
  delay(7); // frequency of 100Hz - take average of 5 samples
  if (Serial.available()) {
    is_connected = false;
    threeWayHandshake();
  }
  else
  {
    //Read accelerometer data:
    Wire.beginTransmission(MPU);
    Wire.write(0x3B); //Start with ACCEL_XOUT_H
    Wire.endTransmission(false);
    Wire.requestFrom(MPU, 6, true); //Read 6 registers in total, each axis value is stored in 2 registers
    //For a range of +-2g, we need to divide the raw values by 16384, according to the datasheet
    AccX = (Wire.read() << 8 | Wire.read()) / 16384.0; //X-axis value //unit: g
    AccY = (Wire.read() << 8 | Wire.read()) / 16384.0; //Y-axis value
    AccZ = (Wire.read() << 8 | Wire.read()) / 16384.0; //Z-axis value
    //Correct the outputs with the calc error values:
    AccX = (AccX - 0.05) * 9.81; //Convert to ms^-2
    AccY = AccY * 9.81;
    AccZ = (AccZ - 0.07)* 9.81;
    AccXSum += AccX;
    AccYSum += AccY;
    AccZSum += AccZ;
    
    //Read Gyroscope Data:
    previousTime = currentTime; //Previous Time is stored before actual time is read
    currentTime = millis(); //Current Time actual time read
    elapsedTime = (currentTime - previousTime)/1000; //Divide by 1000 to get seconds
  
    Wire.beginTransmission(MPU);
    Wire.write(0x43); //Gyro Data First Register address 0x43
    Wire.endTransmission(false);
    Wire.requestFrom(MPU, 6, true); //read 4 registers total, each axis value is stored in 2 registers
    //For a 250 deg/s range, divide the raw value by 131.0, according to datasheet
    GyroX = (Wire.read() << 8 | Wire.read()) / 131.0; //unit: deg/s
    GyroY = (Wire.read() << 8 | Wire.read()) / 131.0;
    GyroZ = (Wire.read() << 8 | Wire.read()) / 131.0;
    //Correct the outputs with the calc error values:
    GyroX = GyroX + 0.89;
    GyroY = GyroY - 0.79;
    GyroZ = GyroZ - 1.84;
    GyroXSum += GyroX;
    GyroYSum += GyroY;
    GyroZSum += GyroZ;
    
    middleFlex = analogRead(middleFinger);
    float middleVflex = middleFlex * VCC / 1023.0;
    float middleRflex = R_DIV * (VCC / middleVflex - 1.0);
    int middleAngle = map(middleRflex, middleFlatResistance, middleBendResistance, 0, 90.0);
    middleAngleSum += middleAngle;
    
    lastFlex = analogRead(lastFinger);
    float lastVflex = lastFlex * VCC / 1023.0;
    float lastRflex = R_DIV * (VCC / lastVflex - 1.0);
    int lastAngle = map(lastRflex, lastFlatResistance, lastBendResistance, 0, 90.0);
    lastAngleSum += lastAngle;

    count++;
    count%=5;
    if(count == 4) {
      AccXSum /= 5;
      AccYSum /= 5;
      AccZSum /= 5;
      GyroXSum /= 5;
      GyroYSum /= 5;
      GyroZSum /= 5;

      int data[8];
      data[0] = GyroXSum;
      data[1] = GyroYSum;
      data[2] = GyroZSum;
      data[3] = AccXSum*100;
      data[4] = AccYSum*100;
      data[5] = AccZSum*100;
      data[6] = middleAngleSum/5;
      data[7] = lastAngleSum/5;

      AccXSum = 0;
      AccYSum = 0;
      AccZSum = 0;
      GyroXSum = 0;
      GyroYSum = 0;
      GyroZSum = 0;
      middleAngleSum = 0;
      lastAngleSum = 0;

      sendDataPacket(data); 
    }
  }
}
