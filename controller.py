from bluno_beetle import BlunoBeetle
from bluno_beetle_udp import BlunoBeetleUDP
import threading

class Controller:
    def __init__(self, params):
        self.beetles = [BlunoBeetle(params[0]), BlunoBeetle(params[1]), BlunoBeetleUDP(params[2])]

    def run_threads(self):
        self.threads = [
            threading.Thread(target=self.beetles[0].bluno_beetle_main, args=()),
            threading.Thread(target=self.beetles[1].bluno_beetle_main, args=()),
            threading.Thread(target=self.beeltes[2].bluno_beetle_main, args=())
        ]

        for thread in self.threads:
            thread.start()
