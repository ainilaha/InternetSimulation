from struct import pack, unpack, calcsize

import struct

ETH_HDR_FMT = '!6s6sH'

'''
Simple Python model for an Ethernet Frame
'''


class EthernetFrame:
    def __init__(self, dest_mac='', src_mac='', tcode=0x0800, data=''):
        self.eth_dest_addr = dest_mac
        self.eth_src_addr = src_mac
        self.eth_tcode = tcode  # Transaction Code, 0x0800 is DOD Internet Protocol (IP) others can refer
                                # http://www.cavebear.com/archive/cavebear/Ethernet/type.html
        self.data = data

    def __repr__(self):
        repr = ('EthFrame: ' +
                '[dest_mac: %s, src_mac: %s, tcode: 0x%04x,' +
                ' len(data): %d]') \
               % (self._eth_addr(self.eth_dest_addr),
                  self._eth_addr(self.eth_src_addr),
                  self.eth_tcode, len(self.data))
        return repr

    def pack(self):
        eth_header = pack(ETH_HDR_FMT,
                          self.eth_dest_addr, self.eth_src_addr,
                          self.eth_tcode)
        eth_frame = ''.join([eth_header, self.data])
        return eth_frame

    def unpack(self, eth_frame):
        hdr_len = calcsize(ETH_HDR_FMT)
        eth_headers = eth_frame[:hdr_len]
        eth_fields = unpack(ETH_HDR_FMT, eth_headers)
        self.eth_dest_addr = eth_fields[0]
        self.eth_src_addr = eth_fields[1]
        self.eth_tcode = eth_fields[2]
        self.data = eth_frame[hdr_len:]

    def _eth_addr(self, raw):
        hex = '%.2x:%.2x:%.2x:%.2x:%.2x:%.2x' \
              % (ord(raw[0]), ord(raw[1]), ord(raw[2]),
                 ord(raw[3]), ord(raw[4]), ord(raw[5]))
        return hex


if __name__ == "__main__":
    # 7b-4c-95-23-e8-89
    test_mac = struct.pack('!6B',
                           int('7b', 16), int('4c', 16), int('95', 16),
                           int('23', 16), int('e8', 16), int('89', 16))
    print test_mac
    print unpack('!6B', test_mac)
    e = EthernetFrame(test_mac, test_mac, data="test data Frame")
    print e.__repr__()
    test_mac = struct.pack('!6B',
                           int('7b', 16), int('4c', 16), int('95', 16),
                           int('23', 16), int('e8', 16), int('88', 16))
    print e._eth_addr(test_mac)
