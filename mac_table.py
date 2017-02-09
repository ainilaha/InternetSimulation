from netaddr import EUI


class MacRow:
    def __init__(self, ip, mac, mac_type):
        self.ip = ip
        self.mac = mac
        self.mac_type = mac_type  # Dynamic or Static


'''
MACTable simulated an MAC table or ARP cache table

'''


class MACTable:
    def __init__(self):
        self.mac_table = []


    '''
    Only same MAC or broadcast address considered as matched addresses
    in real case may use something like src_mac & dest_mac == src_mac
    '''
    def match_mac(self, dest_mac):
        for mac_row in self.mac_table:
            if EUI(dest_mac) == EUI(mac_row.mac) or EUI(dest_mac) == EUI("FF-FF-FF-FF-FF-FF"):
                return True

        return False


if __name__ == "__main__":
    print type(EUI("00-1B-77-49-54-FD").bin)
    mt = MACTable()
    mr1 = MacRow("1.1.1.1","00-1B-77-49-54-F2","Static")
    mr2 = MacRow("1.1.1.2", "00:1B:77:49:54:FD", "Dynamic")
    mr3 = MacRow("1.1.1.3", "00-1B-77-49-54-FF", "Static")
    mt.mac_table.append(mr1)
    mt.mac_table.append(mr2)
    mt.mac_table.append(mr3)
    print mt.match_mac("00-1B-77-49-54-FD")
