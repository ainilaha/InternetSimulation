import multiprocessing
import os
import binascii
import threading
import time

import struct
from enum import Enum
from Queue import Empty

from arp_mac_table import ARPnMACRow, ARPnMACTable
from netaddr import EUI
from netaddr import IPAddress

from arp import ARPPacket
from ethernet import EthernetFrame
from ip import IPDatagram
from routing_table import RoutingTable

'''
Interface class simulated an interface of a router. Each interface hold a send out queue to address packets.
However, there is no receive queue in an interface since all received packets will go to the total queue
in the router.
Note: Here I am using a state control variable to simulated an interface interrupt in real OS

'''


class State(Enum):
    BESSY = 0
    AVAIlIBBIE = 1
    NO_CONNECTED = 2


class Interface:
    def __init__(self):
        self.type = 0  # faster 0  ser 1
        self.name = ""  # faster 0/0, faster 1/1, ser 0/0, ser 0/1
        self.mac = ""
        self.ip_addr = "0.0.0.0"
        self.STATE = State.AVAIlIBBIE
        self.send_frame_queue = multiprocessing.Queue()
        self.router = None

    def _send(self):
        print "starting receiving frame....."
        time.sleep(0.01)
        while True:
            try:
                data_frame = self.send_frame_queue.get()
                self.send_frame(data_frame)
            except Empty:
                pass
            finally:
                self._send()

    def send_frame(self, data_frame):
        eth_frame = EthernetFrame(src_mac="", dest_mac="")
        eth_frame.unpack(data_frame)
        ip_data = IPDatagram("", "", data="")
        ip_data.unpack(eth_frame.data)
        dest_mac_row = self.router.arp_mac_table.get_mac_from_table(ip_data.ip_dest_addr)
        if dest_mac_row:
            eth_frame.eth_dest_addr = dest_mac_row.mac
            dest_mac_row.interface.router.received_frame_data_queue.put(eth_frame.pack())
            return
        else:
            dest_ip = ip_data.ip_dest_addr
            dest_mac = self.send_arp_request(dest_ip)
            print "update_mac_table" + dest_mac

    def send_arp_request(self, dest_ip_addr):
        spa = self.ip_addr
        sha = self.mac
        tpa = dest_ip_addr
        # pack the ARP broadcast mac address
        tha = struct.pack('!6B',
                          int('FF', 16), int('FF', 16), int('FF', 16),
                          int('FF', 16), int('FF', 16), int('FF', 16))
        # pack ARP request
        arp_packet = ARPPacket(sha=sha, spa=spa, tha=tha, tpa=tpa)
        eth_data = arp_packet.pack()
        # pack Ethernet Frame: 0x0806 wrapping ARP packet
        eth_frame = EthernetFrame(dest_mac=tha, src_mac=sha, tcode=0x0806, data=eth_data)
        print('Sending ARP REQUEST for the gateway MAC:' +
              '\n\t%s\n\t%s' % (arp_packet, eth_frame))
        print('Querying gateway MAC address, %s' % arp_packet)
        phy_data = eth_frame.pack()
        self.send_frame(phy_data)

        while True:
            try:
                packet = self.router.received_frame_data_queue.get(0)
                eth_frame.unpack(packet)
                if eth_frame.eth_tcode == 0x0806:
                    break
            except Empty:
                pass
        arp_packet.unpack(eth_frame.data)
        print('Receiving ARP REPLY of the gateway MAC:' +
              '\n\t%s\n\t%s' % (arp_packet, eth_frame))
        print('Get gateway MAC address, %s' % arp_packet)
        return arp_packet.arp_sha


'''
RouterSimulator class simulated an Router in simple way.

'''


class RouterSimulator:
    def __init__(self, name):
        self.intList = []  # interface list
        self.name = name
        self.message_content = ""
        self.chat_window = None
        self.route_table = RoutingTable()
        self.arp_mac_table = ARPnMACTable()
        self.config_file_path = "config/" + self.name
        self.arp_mac_table_path = "config/" + self.name + "_apr_mac"
        self.initialize_router()
        self.received_datagram_queue = multiprocessing.Queue()
        self.received_frame_data_queue = multiprocessing.Queue()
        # self.arp = self.pool.apply_async(self.reply_arp, ())  # start arp request listening
        self.arp = threading.Thread(target=self.reply_arp)
        self.arp.start()

    def initialize_router(self):
        int_name_list = "faster 0/0", "faster 1/1", "ser 0/0", "ser 0/1"
        int_type_list = (1, 1, 0, 0)
        for i in range(0, 4):  # each router equiped with four ports
            mac = binascii.b2a_hex(os.urandom(6))  # random generate 48-bit Mac Address presented by 12 hex numbers
            interface = Interface()
            interface.mac = str(EUI(mac))
            interface.router = self
            interface.name = int_name_list[i]
            interface.type = int_type_list[i]
            self.intList.append(interface)
        self.load_config()

    def save_config(self):
        if os.path.exists(self.config_file_path):
            os.remove(self.config_file_path)
        conf_file = open(self.config_file_path, 'a+')  # Trying to create a new file or open one
        print len(self.intList)
        for port in self.intList:
            conf_file.write(port.name + " : " + str(port.type) + " : " + port.ip_addr + " : " + port.mac + os.linesep)
        conf_file.close()
        self.init_arp_mac_table()
        self.arp_mac_table.save_table(self.arp_mac_table_path)

    def load_config(self):
        if os.path.exists(str(self.config_file_path)):
            conf_file = open(self.config_file_path, 'r')
            i = 0
            for line in conf_file.readlines():
                line = line.split(":")
                self.intList[i].name = str(line[0]).strip()
                self.intList[i].type = str(line[1]).strip()
                self.intList[i].ip_addr = str(line[2]).strip()
                self.intList[i].mac = str(line[3]).strip()
                i += 1
            self.arp_mac_table.mac_table = []
            self.arp_mac_table.load_table_config(self.arp_mac_table_path, self.intList)

    def show_config(self):
        for port in self.intList:
            print port.name + " : " + str(port.type) + " : " + port.ip_addr + " : " + port.mac + "\n"
            print "----------------------------------------\n"

    def reply_arp(self):
        print "Listening ARP.... "
        time.sleep(0.1)
        arp_frame = EthernetFrame(dest_mac="", src_mac="")
        arp_packet = ARPPacket(sha="", tha="", spa="")
        while True:
            try:
                arp_frame_raw = self.received_frame_data_queue.get()
                arp_frame.unpack(arp_frame_raw)
                print "from reply_arp:" + arp_frame.__repr__()
                arp_packet.unpack(arp_frame.data)
                print "from reply_arp++:" + arp_packet.__repr__()
                # arp_packet = arp_frame.data
                for inter in self.intList:
                    if IPAddress(arp_packet.arp_tpa) == IPAddress(inter.IP):
                        arp_packet.arp_sha = inter.mac
                        for mac_row in self.arp_mac_table.mac_table:
                            if EUI(mac_row.mac) == EUI(arp_frame.eth_src_addr):
                                mac_row.interface.receive_queue.put(arp_packet.pack())
            except Empty:
                pass
            finally:
                self.reply_arp()

    def receive_frame(self):
        print "starting receiving frame....."
        time.sleep(0.01)
        data_frame = EthernetFrame(dest_mac="", src_mac="")
        while True:
            try:
                ip_data_frame = self.received_frame_data_queue.get()
                data_frame.unpack(ip_data_frame)
                print "receive_frame:" + data_frame.__repr__()
                if 0x0800 == data_frame.eth_tcode:
                    self.received_datagram_queue.put(ip_data_frame)
            except Empty:
                pass
            finally:
                self.receive_frame()

    def route_ip_datagram(self):
        time.sleep(0.01)
        ip_data = IPDatagram("", "", data="")
        data_frame = EthernetFrame(dest_mac="", src_mac="")
        while True:
            try:
                ip_data_frame = self.received_frame_data_queue.get()
                data_frame.unpack(ip_data_frame)
                ip_data.unpack(ip_data_frame.data)
                inter_ip = self.route_table.find_longest_match_network(ip_data.ip_dest_addr)
                for interface in self.intList:
                    if IPAddress(interface.ip_addr) == IPAddress(inter_ip):
                        interface.send_frame_queue.put(data_frame.pack())
            except Empty:
                pass
            finally:
                self.route_ip_datagram()

    def init_arp_mac_table(self):
        if len(self.arp_mac_table.mac_table) == 0:
            for inter in self.intList:
                arp_n_mac_row = ARPnMACRow(ip_addr=inter.ip_addr, mac=inter.mac, mac_type=1, age=-1)
                arp_n_mac_row.interface = inter
                self.arp_mac_table.mac_table.append(arp_n_mac_row)
        else:
            for i in range(0, 4):
                if str(self.arp_mac_table.mac_table[i].interface.name).strip() == str(self.intList[i].name).strip():
                    self.arp_mac_table.mac_table[i].inter = self.intList[i]
                    self.arp_mac_table.mac_table[i].ip_addr = self.intList[i].ip_addr
                    self.arp_mac_table.mac_table[i].mac = self.intList[i].mac


def main():
    test_mac = struct.pack('!6B',
                           int('7b', 16), int('4c', 16), int('95', 16),
                           int('23', 16), int('e8', 16), int('89', 16))
    tha = struct.pack('!6B',
                      int('FF', 16), int('FF', 16), int('FF', 16),
                      int('FF', 16), int('FF', 16), int('FF', 16))
    ip = struct.pack('4B', 101, 104, 10, 10)
    router = RouterSimulator("Router1")
    arp_packet = ARPPacket(sha=test_mac, spa=ip, tha=tha, tpa=ip)
    print arp_packet.__repr__()
    e = EthernetFrame(test_mac, test_mac, tcode=0x0806, data=arp_packet.pack())
    print e.__repr__()
    router.received_frame_data_queue.put(e.pack())
    router.received_frame_data_queue.put(e.pack())
    router.received_frame_data_queue.put(e.pack())
    time.sleep(15)
    router.received_frame_data_queue.put(e.pack())
    router.arp.join()


if __name__ == "__main__":
    main()
