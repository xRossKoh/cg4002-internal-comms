from bluno_beetle import BlunoBeetle
from bluno_beetle_udp import BlunoBeetleUDP

import threading
import time

LINE_UP = '\033[F'

class Controller:
    def __init__(self, params):
        self.beetles = [
                BlunoBeetle(params[0]), 
                BlunoBeetle(params[1]), 
                BlunoBeetleUDP(params[2])
            ]
        self.start_time = 0
        self.prev_processed_bit_count = 0

    def print_statistics(self):
        while True:
            for i in range(20):
                print(LINE_UP, end="")

            print("***********************************************************************************************************")
            processed_bit_count = 0
            fragmented_packet_count = 0
            for beetle in self.beetles:
                processed_bit_count += beetle.get_processed_bit_count()
                fragmented_packet_count += beetle.get_fragmented_packet_count()
                beetle.print_beetle_info()

            print("Statistics".ljust(80))
            print("Data rate: {} kbps".ljust(80).format((processed_bit_count / 1000) / (time.perf_counter() - self.start_time)))
            self.prev_processed_bit_count = processed_bit_count
            self.prev_time = time.perf_counter()
            print("No. of fragmented packets: {}".ljust(80).format(fragmented_packet_count))
            print("************************************************************************************************************")

    def run_threads(self):
        self.threads = []
        for i in range(3):
            self.threads.append(threading.Thread(target=self.beetles[i].bluno_beetle_main, args=()))

        self.threads.append(threading.Thread(target=self.print_statistics, args=()))
        
        for i in range(20):
            print()

        self.start_time = time.perf_counter()
        for thread in self.threads:
            thread.start() 
