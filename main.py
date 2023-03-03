from bluno_beetle import BlunoBeetle
from bluno_beetle_udp import BlunoBeetleUDP
from _socket import SHUT_RDWR
from constant import LINE_UP
from queue import Queue

import os
import socket
import base64
import sys
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
        
        self.beetles = [
                BlunoBeetle(params[0]), 
                BlunoBeetle(params[1]), 
                BlunoBeetleUDP(params[2])
            ]

        # Packet buffer for ext comms
        self.packet_queue = Queue()
        
        # For statistics calculation
        self.start_time = 0
        self.prev_time = 0
        self.prev_processed_bit_count = 0
        self.current_data_rate = 0
       
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
  
    def run_threads(self):
        # create thread for printing statistics
        print_thread = threading.Thread(target=self.print_statistics, args=())

        for i in range(27):
            print()

        self.start_time = time.perf_counter()

        for i in range(3):
            self.beetles[i].start()

        print_thread.start()
    
    # run() function invoked by thread.start()
    def run(self):
        self.setup()
        self.run_threads()

        while not self.shutdown.is_set():
            try:
                #message = input("Enter message to be sent: ")
                #if message == 'q':
                #    break
                if not BlunoBeetle.packet_queue.empty():
                    self.client_socket.send(BlunoBeetle.packet_queue.get())
            except Exception as _:
                # traceback.print_exc()
                self.close_connection()
    
    # prints beetle data and statistics to std output
    def print_statistics(self):
        while True:
            for i in range(27):
                print(LINE_UP, end="")

            print("***********************************************************************************************************")
            processed_bit_count = 0
            fragmented_packet_count = 0
            for beetle in self.beetles:
                processed_bit_count += beetle.get_processed_bit_count()
                fragmented_packet_count += beetle.get_fragmented_packet_count()
                beetle.print_beetle_info()

            print("Statistics".ljust(80))
            current_time = time.perf_counter()
            if current_time - self.prev_time >= 1:
                self.current_data_rate = ((processed_bit_count - self.prev_processed_bit_count) / 1000) / (current_time - self.prev_time)
                self.prev_time = current_time
                self.prev_processed_bit_count = processed_bit_count
            print("Current data rate: {} kbps".ljust(80).format(self.current_data_rate))
            print("Average Data rate: {} kbps".ljust(80).format(
                (processed_bit_count / 1000) / (current_time - self.start_time)
            ))
            print("No. of fragmented packets: {}".ljust(80).format(fragmented_packet_count))
            print("************************************************************************************************************")


if __name__ == '__main__':
    controller = Controller([
        (1, "c4:be:84:20:1a:51"),   # P1 gun (IR transmitter)
        (2, "b0:b1:13:2d:d6:37"),   # P1 vest (IR receiver)
        (3, "c4:be:84:20:19:4c")    # P1 glove (IMU and flex sensors)
        #(4, ""),                   # P2 gun (IR transmitter)
        #(5, ""),                   # P2 vest (IR receiver)
        #(6, "")                    # P2 glove (IMU and flex sensors)
    ])
    controller.start()
   
