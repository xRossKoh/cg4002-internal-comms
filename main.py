import sys

# importing necessary module directories
sys.path.append('/home/kenneth/Desktop/CG4002/scripts/bluno_beetle')
sys.path.append('/home/kenneth/Desktop/CG4002/scripts/helper')

from bluno_beetle import BlunoBeetle
from bluno_beetle_game_state import BlunoBeetleGameState
from bluno_beetle_udp import BlunoBeetleUDP
from player import Player
from game_state import GameState
from _socket import SHUT_RDWR
from collections import deque

import constant
import socket
import threading
import traceback
import time

class Controller(threading.Thread):
    def __init__(self, params):
        super().__init__()
        
        # Create a TCP/IP socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.client_socket = client_socket
        self.connection = client_socket.connect(("localhost" , 8080))
        self.secret_key = None
        self.secret_key_bytes = None

        # Flags
        self.shutdown = threading.Event()
        
        self.players = []
        for param in params:
            self.players.append(Player(param))
            Player.players_game_state.append(GameState())

        """
        self.beetles = [
                BlunoBeetleGameState(params[0]), 
                BlunoBeetleGameState(params[1]), 
                BlunoBeetleUDP(params[2])
            ]
        
        # For statistics calculation
        self.start_time = 0
        self.prev_time = 0
        self.prev_processed_bit_count = 0
        self.current_data_rate = 0

        #self.data = b''

        #self.client = Client()
        """

    def setup(self):
        print('Setting up Secret Key')
        print('Default Secret Key: chrisisdabest123')

        secret_key = 'chrisisdabest123'

        self.secret_key = secret_key
        self.secret_key_bytes = bytes(str(secret_key), encoding='utf-8')

    def close_connection(self):
        self.connection.shutdown(SHUT_RDWR)
        self.connection.close()
        self.shutdown.set()
        self.client_socket.close()

        print("Shutting Down Connection")
    
    def receive_game_state(self):
        while not self.shutdown.is_set():
            message = self.client_socket.recv(128)
            if len(message) > 0:
                print(message)

    def run_threads(self):
        # create thread for printing statistics
        print_thread = threading.Thread(target=self.print_statistics, args=())
        receive_thread = threading.Thread(target=self.receive_game_state, args=()) 
        for i in range(constant.STD_OP_LINES):
            print()

        self.start_time = time.perf_counter()

        #self.client.start()

        for beetle in self.beetles:
            beetle.start()

        print_thread.start()
        #receive_thread.start()
    
    # run() function invoked by thread.start()
    def run(self):
        #self.setup()
        #self.run_threads()
        for player in self.players:
            player.start()

        while not self.shutdown.is_set():
            try:
                #data = input("Enter char: ")

                if not BlunoBeetle.packet_queue:
                    continue
                
                data = BlunoBeetle.packet_queue.popleft()
                #print(data)
                self.client_socket.send(data)
            except Exception as _:
                # traceback.print_exc()
                #self.close_connection()
                continue
    """    
    # prints beetle data and statistics to std output
    def print_statistics(self):
        while True:
            for i in range(constant.STD_OP_LINES):
                print(constant.LINE_UP, end="")

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
        """

if __name__ == '__main__':
    controller = Controller((
            (0,
            [1, constant.P1_IR_TRANSMITTER],     # P1 gun (IR transmitter)
            #[0, 2, constant.P2_IR_RECEIVER],        # P2 vest (IR receiver)
            [2, constant.P1_IR_RECEIVER],        # P1 vest (IR receiver)
            [3, constant.P1_IMU_SENSOR]),       # P1 glove (IMU and flex sensors)
            #(1,
            #[4, constant.P2_IR_TRANSMITTER],     # P2 gun (IR transmitter)
            #[5, constant.P2_IR_RECEIVER],        # P2 vest (IR receiver)
            #[6, constant.P2_IMU_SENSOR])          # P2 glove (IMU and flex sensors)
            ))
    controller.start()
