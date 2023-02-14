from bluno_beetle import BlunoBeetle

import time

class Scheduler:
    def __init__(self, params):
        self.beetles = []
        self.start_times = []
        for param in params:
            self.beetles.append(BlunoBeetle(param))
            self.start_times.append(0)

    def connect(self):
        for beetle in self.beetles:
            beetle.connect()

    def disconnect(self):
        for beetle in self.beetles:
            beetle.disconnect()

    def reconnect(self):
        for beetle in self.beetles:
            beetle.reconnect()

    def main(self):
        for start_time in self.start_times:
            start_time = time.perf_counter()

        while True:
            for i in range(3):
                self.beetles[i].wait_for_data()

scheduler = Scheduler([
    (1, "b0:b1:13:2d:d3:79"),   # ir_transmitter
    #(1, "b0:b1:13:2d:b6:3d"),   // ir_transmitter 
    (2, "b0:b1:13:2d:d6:37"),   # ir_receiver
    (3, "c4:be:84:20:1b:09")    # imu_sensor
])
scheduler.connect()
scheduler.main()
