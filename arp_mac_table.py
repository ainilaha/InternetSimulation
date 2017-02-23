import os
import socket

import struct
from netaddr import EUI
from netaddr import IPAddress


'''
ARPnMACTable simulated an MAC table and ARP cache table
In real network we have ARP table (Layer3) and MAC table (Layer)
usually expire after 2-4 hours and 5 minutes respectively.
But I will just one table to simulated these two table and set them as static(included permanent) and dynamic.

eg
R2#show arp
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  1.1.1.1                23   0000.0000.0001  ARPA   FastEthernet0/0
Internet  1.1.1.2                 -   0000.0000.0002  ARPA   FastEthernet0/0

2960-1#show mac address-table
          Mac Address Table
-------------------------------------------
Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
   1    00ld.70ab.5d60    DYNAMIC     Fa0/2
   1    00le.f724.al60    DYNAMIC     Fa0/3
Total Mac Addresses for this criterion: 2


'''

# dynamic mac row should be expire 5 minutes


class ARPnMACRow:
    def __init__(self, ip_addr, mac, mac_type, inter_name, age=-1):
        self.ip_addr = ip_addr
        self.mac = mac
        self.mac_type = mac_type  # Dynamic:0  or Static:1
        self.age = age  # minutes  -1 is static ( or permanent)
        self.inter_name = inter_name


class ARPnMACTable:
    def __init__(self):
        self.mac_table = []
        self.router_list = []
        self.host_list = []

    '''
    Only same MAC or broadcast address considered as matched addresses
    in real case may use something like src_mac & dest_mac == src_mac
    '''

    @staticmethod
    def match_mac(src_mac, dest_mac):
            if EUI(dest_mac) == EUI(src_mac) or EUI(dest_mac) == EUI("FF-FF-FF-FF-FF-FF"):
                return True
            else:
                return False

    def get_mac_from_table(self, dest_ip):
        # dest_ip = str(socket.inet_ntoa(dest_ip))
        print "--------------get_mac_from_table--------------------"
        for mac_row in self.mac_table:
            print str(IPAddress(mac_row.ip_addr)) + ":" + mac_row.mac + " : " + str(IPAddress(dest_ip))
            if IPAddress(mac_row.ip_addr) == IPAddress(dest_ip):
                return mac_row
        return None

    def update_mac(self, mac, dest_ip, inter_name):
        mac_row = ARPnMACRow(ip_addr=str(socket.inet_ntoa(dest_ip)), mac=str(EUI(mac)),
                             inter_name=inter_name, mac_type=0, age=5)
        self.mac_table.append(mac_row)
        self.show_table()

    @staticmethod
    def get_mac_pack(mac):
        mac = mac.split("-")
        mac_puck = struct.pack('!6B', int(str(mac[0]).strip(), 16), int(str(mac[1]).strip(), 16),
                               int(str(mac[2]).strip(), 16), int(str(mac[3]).strip(), 16),
                               int(str(mac[4]).strip(), 16), int(str(mac[5]).strip(), 16))
        return mac_puck

    def show_table(self):
        for mac_row in self.mac_table:
            print"%s : %s : %s : %d : %d " % (mac_row.ip_addr, mac_row.inter_name,
                                              mac_row.mac, mac_row.mac_type, mac_row.age)

    def save_table(self, mac_config_path):
        if os.path.exists(mac_config_path):
            os.remove(mac_config_path)
        conf_file = open(mac_config_path, 'a+')
        for mac_row in self.mac_table:
            line = "%s : %s : %s : %d : %d \n" % (mac_row.ip_addr, mac_row.mac,
                                                  mac_row.inter_name, mac_row.mac_type, mac_row.age)
            conf_file.write(line)
        conf_file.close()

    def load_table_config(self, mac_config_path):
        if os.path.exists(mac_config_path):
            config_file = open(mac_config_path, "r")
            for line in config_file.readlines():
                line = line.split(":")
                mac_row = ARPnMACRow(ip_addr=line[0].strip(), mac=line[1].strip(), mac_type=int(line[3].strip()),
                                     inter_name=line[2].strip(), age=int(line[4].strip()))
                self.mac_table.append(mac_row)

if __name__ == "__main__":
    print type(EUI("00-1B-77-49-54-FD").bin)
    mt = ARPnMACTable()
    mr1 = ARPnMACRow("1.1.1.1", "00-1B-77-49-54-F2", 1)

    mr2 = ARPnMACRow("1.1.1.2", "00:1B:77:49:54:FD", 1)

    mr3 = ARPnMACRow("1.1.1.3", "00-1B-77-49-54-FF", 1)

    mt.mac_table.append(mr1)
    mt.mac_table.append(mr2)
    mt.mac_table.append(mr3)
    mt.show_table()

