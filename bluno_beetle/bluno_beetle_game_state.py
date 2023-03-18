from bluno_beetle import BlunoBeetle
from packet_type import PacketType
from constant import PACKET_SIZE

import time

class BlunoBeetleGameState(BlunoBeetle):
    def __init__(self, params):
        super().__init__(params)

        # next expected seq no from beetle
        self.seq_no = 0
    
    #################### Packet generation ####################

    def generate_game_state_packet(self, packet_type):
        node_id = self.node_id
        header = (node_id << 4) | (packet_type << 2) | self.seq_no
        data = [header, 
                BlunoBeetle.players[0].bullets, 
                BlunoBeetle.players[0].health,
                0, 0, 0, 0, 0]
        data[7] = self.crc.calc(self.ble_packet.pack(data))
        return self.ble_packet.pack(data)

    #################### Packet sending ####################

    def send_game_state_packet(self, packet_type):
        self.send_packet(self.generate_game_state_packet(packet_type))

    #################### Checks ####################

    def seq_no_check(self):
        return self.ble_packet.get_seq_no() == self.seq_no

    def process_data(self):
        self.ble_packet.unpack(self.delegate.extract_buffer())
        self.print_test_data()
        print("Processing data")
        print(self.seq_no_check())
        if self.crc_check() and self.packet_check(PacketType.DATA) and self.seq_no_check():            
             # increment seq no
            self.seq_no += 1
            self.seq_no %= 2

            # for testing
            #self.print_test_data()

            self.add_packet_to_queue()
        
        # incorrect packet will send with old seq no
        # correct packet will send with new seq no
        #self.send_game_state_packet(PacketType.ACK)
    
    def three_way_handshake(self):
        while not self.is_connected:
            self.send_game_state_packet(PacketType.HELLO)
            #print("Initiated 3-way handshake with beetle {}...\r".format(self.beetle_id))

            start_time = time.perf_counter()
            tle = False

            # busy wait for response from beetle
            while self.delegate.buffer_len < PACKET_SIZE:
                if self.peripheral.waitForNotifications(0.0005):
                    pass
                elif time.perf_counter() - start_time >= 0.1:
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
            self.send_game_state_packet(PacketType.ACK)

            # change connected state to true
            self.is_connected = True

            # reset seq no
            self.seq_no = 0

            #print("3-way handshake with beetle {} complete.\r".format(self.beetle_id))


    def wait_for_data(self):
        try:
            self.three_way_handshake()
            start_time = time.perf_counter()
            ack_time = time.perf_counter()
            while not self.shutdown.is_set():
                # check for bluetooth communication
                if self.peripheral.waitForNotifications(0.0005):
                    # reset start time if packet is received
                    start_time = time.perf_counter()

                    # check if a full packet is in buffer
                    if self.delegate.buffer_len < PACKET_SIZE:
                        self.fragmented_packet_count += 1 
                    else:
                        # full packet in buffer
                        self.process_data()
                        self.processed_bit_count += PACKET_SIZE * 8
                
                # send game state update every 0.1s if no packet received
                if time.perf_counter() - ack_time >= 0.1:
                    #print("Game state update")
                    self.send_game_state_packet(PacketType.ACK)
                    ack_time = time.perf_counter()

                # no packet received, check for timeout
                #if time.perf_counter() - start_time >= 2.5:
                #    print("Timeout")
                #    self.reconnect()
                #    start_time = time.perf_counter()
                #    ack_time = time.perf_counter()

            # shutdown connection and terminate thread
            self.disconnect()
            print("Beetle ID {} terminated".format(self.beetle_id))
        except Exception as e:
            #print(e)
            self.reconnect()
            self.wait_for_data()

    def run(self):
        self.connect()
        self.wait_for_data()

