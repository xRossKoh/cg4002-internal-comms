from bluno_beetle import BlunoBeetle
from packet_type import PacketType

class BlunoBeetleUDP(BlunoBeetle):
    def __init__(self, params):
        super().__init__(params)

    def process_data(self):
        self.ble_packet.unpack(self.delegate.extract_buffer())
        if self.crc_check() and self.packet_check(PacketType.DATA):
            self.unpack_packet()

        #print("Number of fragmented packet(s): {}".format(self.fragmented_packet_count))

bluno = BlunoBeetleUDP((3, "b0:b1:13:2d:d6:37"))
bluno.connect()
bluno.wait_for_data()
