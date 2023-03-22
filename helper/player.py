from bluno_beetle import BlunoBeetle
from bluno_beetle_udp import BlunoBeetleUDP
from bluno_beetle_game_state import BlunoBeetleGameState
from game_state import GameState
from ble_packet import BLEPacket

import time
import constant
import threading

class Player(threading.Thread):
    # arr of GameState objs to keep track of game state for all players
    # to be instantiated in main.py
    players_game_state = []

    def __init__(self, params):
        super().__init__()

        self.player_id = params[0]
        self.beetles = [    BlunoBeetleGameState([params[0]] + params[1]),    # gun (IR transmitter)
                            BlunoBeetleGameState([params[0]] + params[2]),    # vest (IR receiver)
                            BlunoBeetleUDP([params[0]] + params[3])]          # glove (imu_sensor)
        
        # statistics variables
        self.start_time = 0
        self.prev_time = 0
        self.prev_processed_bit_count = 0
        self.current_data_rate = 0
    
    def update_game_state(self, packet):
        unpacker = BLEPacket()
        unpacker.unpack(packet)
        players_game_state[0].update_game_state(unpacker.get_euler_data()[:2])
        #players_game_state[1].update_game_state(unpacket.get_acc_data()[:2])
 
    # prints beetle data and statistics to std output
    def print_statistics(self):
        while True:
            for i in range(constant.STD_OP_LINES):
                print(constant.LINE_UP, end="")

            print("***********************************************************************************************************")
            print("Player {} - Bullets = {}, Health = {}".ljust(constant.STD_OP_LENGTH).format(
                self.player_id,
                Player.players_game_state[self.player_id].bullets,
                Player.players_game_state[self.player_id].health,
            ))
            print("***********************************************************************************************************")
            processed_bit_count = 0
            fragmented_packet_count = 0
            for beetle in self.beetles:
                processed_bit_count += beetle.get_processed_bit_count()
                fragmented_packet_count += beetle.get_fragmented_packet_count()
                beetle.print_beetle_info()

            print("Statistics".ljust(constant.STD_OP_LENGTH))
            current_time = time.perf_counter()
            if current_time - self.prev_time >= 1:
                self.current_data_rate = ((processed_bit_count - self.prev_processed_bit_count) / 1000) / (current_time - self.prev_time)
                self.prev_time = current_time
                self.prev_processed_bit_count = processed_bit_count
            print("Current data rate: {} kbps".ljust(constant.STD_OP_LENGTH).format(self.current_data_rate))
            print("Average Data rate: {} kbps".ljust(constant.STD_OP_LENGTH).format(
                (processed_bit_count / 1000) / (current_time - self.start_time)
            ))
            print("No. of fragmented packets: {}".ljust(constant.STD_OP_LENGTH).format(fragmented_packet_count))
            print("************************************************************************************************************")

    def run(self):
        # create thread for printing statistics
        print_thread = threading.Thread(target=self.print_statistics, args=())
        
        for i in range(constant.STD_OP_LINES):
            print()

        self.start_time = time.perf_counter()

        for beetle in self.beetles:
            beetle.start()

        print_thread.start()
