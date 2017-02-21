import multiprocessing
import os
import binascii
import socket
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
        self.net_mask = "255.255.255.0"
        self.STATE = State.AVAIlIBBIE
        self.send_queue = multiprocessing.Queue()
        self.received_frame_queue = multiprocessing.Queue()
        self.receive_arp_queue = multiprocessing.Queue()
        self.router = None
        self.send_thread = threading.Thread(target=self._send)
        self.send_thread.start()
        self.receiving = threading.Thread(target=self.receive_frame)
        self.receiving.start()

    def _send(self):
        if self.router:
            print self.router.name + ":" + self.name + ":interface starting send frame....."
        time.sleep(0.01)
        while True:
            try:
                next_ip_n_packets = self.send_queue.get(0)
                self.send_packet(next_ip_n_packets)
            except Empty:
                pass
            finally:
                time.sleep(0.01)
                # self._send()

    def send_frame(self, eth_frame):
        for router in self.router.arp_mac_table.router_list:
            for inter in router.intList:
                inter.received_frame_queue.put(eth_frame)

    def send_packet(self, next_ip_n_packets):
        if len(next_ip_n_packets) == 2:
            ip_data = IPDatagram("", "", data="")
            ip_data.unpack(next_ip_n_packets[1])
            next_ip = next_ip_n_packets[0]
            print self.router.name + ":" + self.name + " : send_frame" + ip_data.__repr__()
            dest_mac_row = self.router.arp_mac_table.get_mac_from_table(next_ip)
            print "------------------send_frame----------------------"
            if dest_mac_row:
                print "-----------if-------send_frame--" + self.mac + "-------------------" + dest_mac_row.mac
                eth_frame = EthernetFrame(src_mac=ARPnMACTable.get_mac_pack(self.mac),
                                          dest_mac=ARPnMACTable.get_mac_pack(dest_mac_row.mac), data=next_ip_n_packets[1])
                print self.router.name + ":" + self.name + " : send_frame2 " + eth_frame.__repr__()
                self.send_frame(eth_frame.pack())
            else:
                print "-----------else-------send_frame----------------------"
                print "next_ip=" + next_ip
                dest_mac = self.send_arp_request(next_ip)
                eth_frame = EthernetFrame(src_mac=ARPnMACTable.get_mac_pack(self.mac),
                                          dest_mac=dest_mac, data=next_ip_n_packets[1])
                print self.router.name + ":" + self.name + " : else eth" + eth_frame.__repr__()
                print self.router.name + ":" + self.name + " : else send_frame" + ip_data.__repr__()
                self.send_frame(eth_frame.pack())
                print self.router.name + " : " + self.name + " : " + "update_mac_table:" + EthernetFrame.eth_addr(dest_mac)
                self.router.arp_mac_table.update_mac(EthernetFrame.eth_addr(dest_mac), ip_data.ip_dest_addr, self.name)
                self.send_packet(next_ip_n_packets[1])

    def receive_frame(self):
        print self.name + ":starting listening and receiving frame....."
        time.sleep(0.01)
        data_frame = EthernetFrame(dest_mac="", src_mac="")
        while True:
            try:
                ip_data_frame = self.received_frame_queue.get()
                data_frame.unpack(ip_data_frame)
               # print self.router.name + " : " + self.name + " : receive_frame:" + data_frame.__repr__()
                dest_mac = EthernetFrame.eth_addr(data_frame.eth_dest_addr)
                if EUI(dest_mac) == EUI(self.mac):
                    if data_frame.eth_tcode == 0x0806:
                        self.receive_arp_queue.put(ip_data_frame)
                    elif data_frame.eth_tcode == 0x0800:
                        self.router.received_frame_data_queue.put(ip_data_frame)
                elif EUI("FF-FF-FF-FF-FF-FF") == EUI(dest_mac):
                    self.reply_arp(ip_data_frame)
            except Empty:
                pass
                # finally:
                #    self.receive_frame()

    def send_arp_request(self, dest_ip_addr):
        print "-----------------------send_arp_request---------------------------"
        spa = socket.inet_aton(self.ip_addr.strip())
        sha = ARPnMACTable.get_mac_pack(self.mac)
        tpa = socket.inet_aton(dest_ip_addr.strip())
        # pack the ARP broadcast mac address
        tha = struct.pack('!6B',
                          int('FF', 16), int('FF', 16), int('FF', 16),
                          int('FF', 16), int('FF', 16), int('FF', 16))
        # pack ARP request
        arp_packet = ARPPacket(sha=sha, spa=spa, tha=tha, tpa=tpa)
        eth_data = arp_packet.pack()
        # pack Ethernet Frame: 0x0806 wrapping ARP packet
        eth_frame = EthernetFrame(dest_mac=tha, src_mac=sha, tcode=0x0806, data=eth_data)
        print self.router.name + " : " + self.name + ":send_arp_request:" + eth_frame.__repr__()
        print self.router.name + " : " + self.name + ":send_arp_request++:" + arp_packet.__repr__()
        phy_data = eth_frame.pack()
        for router in self.router.arp_mac_table.router_list:
            for inter in router.intList:
                inter.received_frame_queue.put(phy_data)
        while True:
            try:
                packet = self.receive_arp_queue.get(0)
                eth_frame.unpack(packet)
                if eth_frame.eth_tcode == 0x0806:
                    break
            except Empty:
                pass
        arp_packet.unpack(eth_frame.data)
        return arp_packet.arp_sha

    def reply_arp(self, eth_frame):
        print self.name + ":Listening ARP.... "
        arp_frame = EthernetFrame(dest_mac="", src_mac="")
        arp_frame.unpack(eth_frame)
        arp_packet = ARPPacket(sha="", tha="", spa="")
        # print self.name + ":request reply =" + arp_frame.__repr__()
        arp_packet.unpack(arp_frame.data)
        # print self.router.name +":" + self.name+":arp="+ arp_packet.__repr__() + "\n\n"
        # print self.name + ":******* =" + str(socket.inet_ntoa(arp_packet.arp_tpa)).strip() +":"+self.ip_addr.strip()
        if str(socket.inet_ntoa(arp_packet.arp_tpa)).strip() == self.ip_addr.strip():
            arp_packet.arp_sha = ARPnMACTable.get_mac_pack(self.mac)
            arp_frame = EthernetFrame(dest_mac=arp_frame.eth_src_addr,
                                      src_mac=ARPnMACTable.get_mac_pack(self.mac), tcode=0x0806, data=arp_packet.pack())
            self.send_frame(arp_frame.pack())


'''
RouterSimulator class simulated an Router in simple way.

'''


class RouterSimulator:
    def __init__(self, name):
        self.intList = []  # interface list
        self.name = name
        self.message_content = ""
        self.route_table = RoutingTable()
        self.arp_mac_table = ARPnMACTable()
        self.config_file_path = "config/" + self.name
        self.arp_mac_table_path = "config/" + self.name + "_apr_mac"
        self.initialize_router()
        self.received_datagram_queue = multiprocessing.Queue()
        self.received_frame_data_queue = multiprocessing.Queue()
        self.receive = threading.Thread(target=self.receive_frame)
        self.receive.start()
        self.routing_packets = threading.Thread(target=self.route_ip_datagram)
        self.routing_packets.start()

    def initialize_router(self):
        int_name_list = "faster 0/0", "faster 1/1", "ser 0/0", "ser 0/1"
        int_type_list = (1, 1, 0, 0)
        for i in range(0, 4):  # each router equipped with four ports
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
            self.arp_mac_table.load_table_config(self.arp_mac_table_path)

    def show_config(self):
        for port in self.intList:
            print port.name + " : " + str(port.type) + " : " + port.ip_addr + " : " + port.mac + "\n"
            print "----------------------------------------\n"

    def receive_frame(self):
        print self.name + ":starting listening and receiving frame....."
        time.sleep(0.01)
        data_frame = EthernetFrame(dest_mac="", src_mac="")
        while True:
            try:
                ip_data_frame = self.received_frame_data_queue.get(0)
                data_frame.unpack(ip_data_frame)
                print self.name + ":from receive_frame:" + data_frame.__repr__()
                if 0x0800 == data_frame.eth_tcode:  # ip protocol
                    self.received_datagram_queue.put(data_frame.data)
            except Empty:
                pass
                # finally:
                #     self.receive_frame()

    def route_ip_datagram(self):
        print self.name + ":starting listening and routing..."
        time.sleep(0.01)
        ip_data = IPDatagram("", "", data="")
        while True:
            try:
                ip_data_packet = self.received_datagram_queue.get()
                ip_data.unpack(ip_data_packet)
                print self.name + ":from route_ip_datagram+:" + ip_data.__repr__()
                dest_ip = socket.inet_ntoa(ip_data.ip_dest_addr)
                print self.name + ":from des_ip+:" + dest_ip
                # inter_ip = self.route_table.find_longest_match_network(dest_ip)
                match_row = self.route_table.find_shortest_path(dest_ip)
                if match_row:
                    print self.name + ":matched interface IP:" + match_row.inter_ip
                    for interface in self.intList:
                        if IPAddress(interface.ip_addr) == IPAddress(match_row.inter_ip):
                            print "matched interface=" + interface.name
                            interface.send_queue.put([match_row.next_ip, ip_data_packet])
                else:
                    print self.name + ":**** dest ip =" + dest_ip + " not reachable or local address!!"

            except Empty:
                pass
                # finally:
                #     self.route_ip_datagram()

    def init_arp_mac_table(self):
        self.arp_mac_table.mac_table = []
        for inter in self.intList:
            arp_n_mac_row = ARPnMACRow(ip_addr=inter.ip_addr, mac=inter.mac, mac_type=1,
                                       inter_name=inter.name, age=-1)
            self.arp_mac_table.mac_table.append(arp_n_mac_row)


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
    e = EthernetFrame(test_mac, test_mac, tcode=0x0806, data=arp_packet.pack())
    router.received_frame_data_queue.put(e.pack())
    time.sleep(1)
    router.received_frame_data_queue.put(e.pack())
    ip = struct.pack('4B', 192, 168, 1, 1)
    ip_data = IPDatagram(ip, ip, data="2879834kjkjdsfrhsdkd233")
    e.data = ip_data.pack()
    e.eth_tcode = 0x0800
    if e.eth_tcode == 0x0800:
        print True
    router.received_frame_data_queue.put(e.pack())
    router.receive.join()
    router.routing_packets.join()
    for interface in router.intList:
        interface.send_thread.join()


if __name__ == "__main__":
    main()
