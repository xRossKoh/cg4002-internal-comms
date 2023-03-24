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

        self.data = b''

    def close_connection(self):
        self.connection.shutdown(SHUT_RDWR)
        self.connection.close()
        self.shutdown.set()
        self.client_socket.close()

        print("Shutting Down Connection")
    
    def receive_game_state(self):
        while not self.shutdown.is_set():
            message = self.client_socket.recv(128)
            
            self.data = self.data + message

            if len(self.data) < constant.PACKET_SIZE:
                continue

            packet = self.data[:constant.PACKET_SIZE]
            self.data = self.data[constant.PACKET_SIZE:]

            Player.update_game_state(packet)

    def run_threads(self):
        # create thread for printing statistics
        receive_thread = threading.Thread(target=self.receive_game_state, args=()) 
        
        for player in self.players:
            player.start()
        
        receive_thread.start()
    
    # run() function invoked by thread.start()
    def run(self):
        self.run_threads()

        while not self.shutdown.is_set():
            try:
                if not BlunoBeetle.packet_queue:
                    continue
                if BlunoBeetle.packet_queue:
                    data = BlunoBeetle.packet_queue.get()
                    self.client_socket.send(data)
            except Exception as _:
                # traceback.print_exc()
                #self.close_connection()
                continue

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
