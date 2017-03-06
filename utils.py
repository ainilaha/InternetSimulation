import time as t

class Timer:
    def __enter__(self):
        self.begin = t.time()
        return self

    def __exit__(self, *args):
        self.duration = t.time() - self.begin


'''
Return the checksum of the given data.
The algorithm comes from:
http://en.wikipedia.org/wiki/IPv4_header_checksum
'''


def checksum(data):
    data_sum = 0
    # pick up 16 bits (2 WORDs) every time
    for i in range(0, len(data), 2):
        # Sum up the ordinal of each WORD with
        # network bits order (big-endian)
        if i < len(data) and (i + 1) < len(data):
            data_sum += (ord(data[i]) + (ord(data[i + 1]) << 8))
        elif i < len(data) and (i + 1) == len(data):
            data_sum += ord(data[i])
    add_on_carry = (data_sum & 0xffff) + (data_sum >> 16)
    result = (~ add_on_carry) & 0xffff
    # swap bytes
    result = result >> 8 | ((result & 0x00ff) << 8)
    return result
