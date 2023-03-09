from bluepy.btle import Peripheral, BTLEDisconnectError
from crc import CRC
from ble_packet import BLEPacket
from read_delegate import ReadDelegate
from struct import *
from packet_type import PacketType
from constant import PACKET_SIZE
from queue import Queue
from game_state import GameState

import threading
import time

class BlunoBeetle(threading.Thread):
    # Class variables
    # Store packets that are ready to be sent via ext comms
    packet_queue = Queue()

    # Variables used to maintain gamestate
    players = [GameState()]

    # threading event for game state change
    # set when game state changes
    # clear when updated game state has been broadcasted to gun and vest
    game_state_changed = [threading.Event()]

    def __init__(self, params):
        super().__init__()

        self.beetle_id = params[0]
        self.node_id = 0
        self.mac_addr = params[1]
        self.write_service_id = 3
        self.write_service = None
        self.delegate = ReadDelegate()
        self.peripheral = Peripheral()
        self.crc = CRC()
        self.ble_packet = BLEPacket()
        self.default_packets = []
        self.is_connected = False
        self.fragmented_packet_count = 0
        self.processed_bit_count = 0
        self.shutdown = threading.Event()

        self.generate_default_packets()
    
    #################### Getter functions ####################

    def get_processed_bit_count(self):
        return self.processed_bit_count

    def get_fragmented_packet_count(self):
        return self.fragmented_packet_count


    #################### BLE connection ####################

    def connect(self):
        try:
            self.peripheral.connect(self.mac_addr)
            #print("Attempting connection with beetle {}...\r".format(self.beetle_id))
            self.peripheral.withDelegate(self.delegate)
            services = self.peripheral.getServices()
            self.write_service = self.peripheral.getServiceByUUID(list(services)[self.write_service_id].uuid)
        except Exception as e:
            #print(e)
            self.connect()
        
    def disconnect(self):
        self.peripheral.disconnect()
        self.delegate.reset_buffer()
        self.is_connected = False

    def reconnect(self):
        for x in range(5):
            self.disconnect()
        #print("Disconnected from beetle {}\r".format(self.beetle_id))
        self.connect()

    def shutdown(self):
        self.shutdown.set()

    #################### Packet generation ####################

    def generate_default_packets(self):
        for i in range(3):
            node_id = self.node_id
            packet_type = i
            header = (node_id << 4) | packet_type
            data = [header, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            data[9] = self.crc.calc(self.ble_packet.pack(data))
            self.default_packets.append(self.ble_packet.pack(data))
    
    def generate_game_state_packet(self):
        node_id = self.node_id
        packet_type = PacketType.DATA
        header = (node_id << 4) | packet_type
        data = [header, 
                BlunoBeetle.players[0].ammo, 
                BlunoBeetle.players[0].health,
                0, 0, 0, 0, 0, 0, 0]
        data[9] = self.crc.calc(self.ble_packet.pack(data))
        return self.ble_packet.pack(data)

    #################### Packet sending ####################

    def send_default_packet(self, packet_type):
        c = self.write_service.getCharacteristics()[0]
        c.write(self.default_packets[int(packet_type)])
    
    #################### Checks ####################

    def crc_check(self):
        crc = self.ble_packet.get_crc()
        self.ble_packet.set_crc(0)
        return crc == self.crc.calc(self.ble_packet.pack())

    def packet_check(self, packet_type):
        try:
            return self.ble_packet.get_beetle_id() == self.beetle_id and PacketType(self.ble_packet.get_packet_type()) == packet_type
        except ValueError:
            # intialize reconnect to reset connection and buffer
            self.reconnect();
            self.wait_for_data();
    
    ################ Print functions ####################
    
    def print_beetle_info(self):
        print("Beetle {}".ljust(80).format(self.beetle_id))
        print(("Status: Connected" if self.is_connected else "Status: Disconnected").ljust(80))
        print("Last processed packet:".ljust(80))
        print("Packet type: {}".ljust(80).format(
            self.ble_packet.get_packet_type()
        ))
        print("Euler data: {}, Acceleration data: {}".ljust(80).format(
            self.ble_packet.get_euler_data(), 
            self.ble_packet.get_acc_data()
        ))
        print("Flex sensor data: {}".ljust(80).format(
            self.ble_packet.get_flex_data()
        ))
        print("************************************************************************************************************")
    
    # for testing
    def print_test_data(self):
        print("Bluno ID: {}, Packet type: {}".format(
            self.ble_packet.get_beetle_id(), 
            self.ble_packet.get_packet_type()
        ))
        print("Euler data: {}, Acceleration data: {}, Flex data: {}".format(
            self.ble_packet.get_euler_data(),
            self.ble_packet.get_acc_data(),
            self.ble_packet.get_flex_data()
        ))

    #################### Communication protocl ####################

    def three_way_handshake(self):
        while not self.is_connected:
            self.send_default_packet(PacketType.HELLO)
            #print("Initiated 3-way handshake with beetle {}...\r".format(self.beetle_id))

            start_time = time.perf_counter()
            tle = False

            # busy wait for response from beetle
            while self.delegate.buffer_len < PACKET_SIZE:
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
                #print("3-way handshake with beetle {} failed.\r".format(self.beetle_id))
                continue

            # else reply with ack
            self.send_default_packet(PacketType.ACK)

            # change connected state to true
            self.is_connected = True

            #print("3-way handshake with beetle {} complete.\r".format(self.beetle_id))
                                  
    def add_packet_to_queue(self):
        BlunoBeetle.packet_queue.put(self.ble_packet.pack())

    def process_data(self):
        self.ble_packet.unpack(self.delegate.extract_buffer())
        if self.crc_check() and self.packet_check(PacketType.DATA):
            self.send_default_packet(PacketType.ACK)
            self.add_packet_to_queue()

            # for testing
            #self.print_test_data()
        else:
            self.send_default_packet(PacketType.NACK)

    def wait_for_data(self):
        try:
            self.three_way_handshake()
            start_time = time.perf_counter()
            while not self.shutdown.is_set():
                if self.peripheral.waitForNotifications(0.0005):
                    # reset start time if packet is received
                    start_time = time.perf_counter()

                    # check if a full packet is in buffer
                    if self.delegate.buffer_len < PACKET_SIZE:
                        self.fragmented_packet_count += 1
                        continue
                    
                    # full packet in buffer
                    self.process_data()
                    self.processed_bit_count += PACKET_SIZE * 8
                    continue

                # no packet received, check for timeout
                if time.perf_counter() - start_time >= 2.5:
                    self.reconnect()
                    start_time = time.perf_counter()

            # shutdown connection and terminate thread
            self.disconnect()
            print("Beetle ID {} terminated".format(self.beetle_id))
        except Exception as e:
            #print(e)
            self.reconnect()
            self.wait_for_data()

    #################### Main function ####################
    def run(self):
        self.connect()
        self.wait_for_data() 
