from bluno_beetle import BlunoBeetle
from packet_type import PacketType

class BlunoBeetleUDP(BlunoBeetle):
    def __init__(self, params):
        super().__init__(params)

    def process_data(self):
        self.ble_packet.unpack(self.delegate.extract_buffer())
        if self.crc_check() and self.packet_check(PacketType.DATA):
            self.add_packet_to_queue()
