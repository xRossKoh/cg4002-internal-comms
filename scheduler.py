from bluno_beetle import BlunoBeetle

class Scheduler:
    def __init__(self, params):
        self.beetle_ids = []
        self.mac_addrs = []
        for param in params:
            self.beetle_ids.append(param[0])
            self.mac_addrs.append(param[1])

    def main(self):
