from bluepy.btle import Peripheral, BTLEDisconnectError
from crc import CRC
from ble_packet import BLEPacket
from read_delegate import ReadDelegate
from struct import *
from packet_type import PacketType

import time

class BlunoBeetle:
    def __init__(self, params):
        self.beetle_id = params[0]
        self.node_id = 0
        self.mac_addr = params[1]
        self.write_service_id = 3
        self.write_service = None
        self.delegate = ReadDelegate()
        self.peripheral = None
        self.crc = CRC()
        self.ble_packet = BLEPacket()
        self.default_packets = []
        self.is_connected = False
        self.fragmented_packet_count = 0;

        self.generate_default_packets()

    def connect(self):
        self.peripheral = Peripheral(self.mac_addr)
        self.peripheral.withDelegate(self.delegate)
        services = self.peripheral.getServices()
        self.write_service = self.peripheral.getServiceByUUID(list(services)[self.write_service_id].uuid)
        
    def disconnect(self):
        self.peripheral.disconnect()
        self.delegate.reset_buffer()
        self.is_connected = False

    def reconnect(self):
        print("Reconnecting...\r")
        for x in range(5):
            self.disconnect()
        self.connect()
    
    def generate_default_packets(self):
        for i in range(3):
            node_id = self.node_id
            packet_type = i
            header = (node_id << 4) | packet_type
            data = [header, 0, 0, 0, 0, 0, 0, 0]
            data[7] = self.crc.calc(self.ble_packet.pack(data))
            self.default_packets.append(self.ble_packet.pack(data))

    def send_default_packet(self, packet_type):
        c = self.write_service.getCharacteristics()[0]
        c.write(self.default_packets[int(packet_type)])

    def crc_check(self):
        crc = self.ble_packet.get_crc()
        self.ble_packet.set_crc(0)
        return crc == self.crc.calc(self.ble_packet.pack())

    def packet_check(self, packet_type):
        return self.ble_packet.get_beetle_id() == self.beetle_id and PacketType(self.ble_packet.get_packet_type()) == packet_type

    def three_way_handshake(self):
        while not self.is_connected:
            self.send_default_packet(PacketType.HELLO)
            print("Initiated 3-way handshake...")

            start_time = time.perf_counter()
            tle = False

            # busy wait for response from beetle
            while self.delegate.buffer_len < 16:
                if self.peripheral.waitForNotifications(0.0005):
                    pass
                elif time.perf_counter() - start_time >= 1.0:
                    tle = True
                    break
                
            if tle:
                continue

            self.ble_packet.unpack(self.delegate.extract_buffer())

            # crc check and packet type check
            if not self.crc_check() or not self.packet_check(PacketType.HELLO):
                print("3-way handshake failed.")
                continue

            # else reply with ack
            self.send_default_packet(PacketType.ACK)

            # change connected state to true
            self.is_connected = True

            print("3-way handshake complete.")
                              
    # for testing
    def unpack_packet(self):
        print("Bluno ID: {}, Packet type: {}".format(self.ble_packet.get_beetle_id(), self.ble_packet.get_packet_type()));

        print("Euler data: {}, Acceleration data: {}".format(self.ble_packet.get_euler_data(), self.ble_packet.get_acc_data()))
         
    def process_data(self):
        self.ble_packet.unpack(self.delegate.extract_buffer())
        if self.crc_check() and self.packet_check(PacketType.DATA):
            self.send_default_packet(PacketType.ACK)
            self.unpack_packet()
        else:
            self.send_default_packet(PacketType.NACK)

        #print("Number of fragmented packet(s): {}".format(self.fragmented_packet_count))

    def wait_for_data(self):
        try:
            self.three_way_handshake()
            start_time = time.perf_counter()
            while True:
                if self.peripheral.waitForNotifications(0.0005):
                    # reset start time if packet is received
                    start_time = time.perf_counter()

                    # check if a full packet is in buffer
                    if self.delegate.buffer_len < 16:
                        self.fragmented_packet_count += 1
                        continue

                    # buffer_len is >= 16
                    self.process_data()
                    continue

                # no packet received, check for timeout
                if time.perf_counter() - start_time >= 2.5:
                    self.reconnect()
                    start_time = time.perf_counter()

                #print("waiting...\r")
        except Exception as e:
            print(e)
            self.reconnect()
            self.wait_for_data()

#bluno = BlunoBeetle((2, "b0:b1:13:2d:d6:37"))
#bluno.connect()
