from bluno_beetle import BlunoBeetle
from bluno_beetle_udp import BlunoBeetleUDP

import threading
import time

LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2k'

class Controller:
    def __init__(self, params):
        self.beetles = [
                BlunoBeetle(params[0]), 
                BlunoBeetle(params[1]), 
                BlunoBeetleUDP(params[2])
            ]
        self.start_time = 0
        self.processed_bit_count = 0
        self.fragmented_packet_count = 0;

    def print_statistics(self):
        while True:
            for i in range(20):
                print(LINE_UP, end=LINE_CLEAR)

            print("************************************************************************************************************")
            for beetle in self.beetles:
                self.processed_bit_count += beetle.get_processed_bit_count()
                self.fragmented_packet_count += beetle.get_fragmented_packet_count()
                beetle.print_beetle_info()

            print("Statistics")
            print("Data rate: {} kbps".format((self.processed_bit_count / 1000) / (time.perf_counter() - self.start_time)))
            print("No. of fragmented packets: {}".format(self.fragmented_packet_count))
            print("************************************************************************************************************")

    def run_threads(self):
        self.threads = []
        for i in range(3):
            self.threads.append(threading.Thread(target=self.beetles[i].bluno_beetle_main, args=()))

        self.threads.append(threading.Thread(target=self.print_statistics, args=()))
        
        for i in range(20):
            print()

        for thread in self.threads:
            thread.start()
