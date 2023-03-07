from bluno_beetle import BlunoBeetle

class BlunoBeetleSNW(BlunoBeetle):
    def __init__(self, params):
        super().__init__(params)

    def process_data(self):
        self.ble_packet.unpack(self.delegate.extract_buffer())
        if self.crc_check() and self.packet_check(PacketType.DATA):
            self.send_default_packet(PacketType.ACK)
            self.add_packet_to_queue()
            # TODO implement Stop-N-Wait for changed game state from ext comms
        else:
            self.send_default_packet(PacketType.NACK)



