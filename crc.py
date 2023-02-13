import struct

class CRC:
    def __init__(self):
        pass

    def calc(self, data):
    
        curr_crc = 0x0000
        sum1 = curr_crc
        sum2 = curr_crc >> 8

        for x in range(16):
            sum1 = (sum1 + data[x]) % 255
            sum2 = (sum2 + sum1) % 255

        return (sum2 << 8) | sum1

    def check(self, packet):
        packet = list(struct.unpack("Bx6hH", packet))
        crc = packet[7]
        packet[7] = 0
        packet = struct.pack("Bx6hH", packet[0], packet[1], packet[2], packet[3], packet[4], packet[5], packet[6], packet[7])
        return self.calc(packet) == crc


