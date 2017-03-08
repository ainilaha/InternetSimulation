from threading import Timer


class DeleteEntryTimer(object):
    def __init__(self, interval, f, entry_list, entry):
        self.interval = interval
        self.f = f
        self.entry_list = entry_list
        self.entry = entry

        self.timer = None

    def callable(self):
        self.f(self.entry_list, self.entry)

    def cancel(self):
        self.timer.cancel()

    def start(self):
        self.timer = Timer(self.interval, self.callable)
        self.timer.start()

    def reset(self):
        self.cancel()
        self.start()


def delete_entry(table_list, entry):
    table_list.remove(entry)


def entry_time_reset(timer_list, entry):
    for timer in timer_list:
        if timer.entry == entry:
            timer.reset()


def checksum(data):
    '''
    Return the checksum of the given data.
    The algorithm comes from:
    http://en.wikipedia.org/wiki/IPv4_header_checksum
    '''

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
