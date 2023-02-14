from bluno_beetle import BlunoBeetle

class Scheduler:
    def __init__(self, params):
        self.beetles = []
        for param in params:
            self.beetles.append(BlunoBeetle(param))

    def connect():
        for beetle in self.beetles:
            beetle.connect()

    def main(self):
        while True:
            for beetle in self.beetles:
                beetle.wait_for_data()

scheduler = Scheduler([
    (1, "b0:b1:13:2d:b6:3d"),   // ir_transmitter 
    (2, "b0:b1:13:2d:d6:37"),   // ir_receiver
    (3, "c4:be:84:20:1b:09")    // imu_sensor
])
