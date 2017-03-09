import multiprocessing
import os
import binascii
import socket
import threading
import time

import struct
from Queue import Empty

from arp_mac_table import ARPnMACRow, ARPnMACTable
from netaddr import EUI
from netaddr import IPAddress

from arp import ARPPacket
from ethernet import EthernetFrame
from interface import Interface
from ip import IPDatagram
from logger import LOG
from rip_simulator import RIPSimulator
from routing_table import RoutingTable

'''
RouterSimulator class simulated an Router in simple way.

'''


class RouterSimulator:
    def __init__(self, name):
        self.intList = []  # interface list
        self.name = name
        self.message_content = ""
        self.route_table = RoutingTable(router=self)
        self.arp_mac_table = ARPnMACTable()
        self.config_file_path = "config/" + self.name
        self.arp_mac_table_path = "config/" + self.name + "_apr_mac"
        self.initialize_router()
        self.received_datagram_queue = multiprocessing.Queue()
        self.received_frame_data_queue = multiprocessing.Queue()
        self.receive = threading.Thread(target=self.receive_frame)
        self.receive.start()
        self.routing_packets = threading.Thread(target=self.route_ip_datagram)  # forwarding IP packets
        self.routing_packets.start()
        self.rip_simulator = RIPSimulator(self)

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
        LOG.info(self.name + "*******************load_config******************************")
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
            self.route_table.init_routing_table(self)

    def show_config(self):
        for port in self.intList:
            LOG.info(port.name + " : " + str(port.type) + " : " + port.ip_addr + " : " + port.mac + "\n")
            LOG.info("----------------------------------------\n")

    def receive_frame(self):
        LOG.info(self.name + ":starting listening and receiving frame.....")
        time.sleep(0.01)
        data_frame = EthernetFrame(dest_mac="", src_mac="")
        while True:
            try:
                ip_data_frame = self.received_frame_data_queue.get(0)
                data_frame.unpack(ip_data_frame)
                LOG.debug(self.name + ":from receive_frame:" + data_frame.__repr__())
                if 0x0800 == data_frame.eth_tcode:  # ip protocol
                    self.received_datagram_queue.put(data_frame.data)
            except Empty:
                pass
                # finally:
                #     self.receive_frame()

    def route_ip_datagram(self):
        LOG.info(self.name + ":starting listening and routing...")
        time.sleep(0.01)
        ip_data = IPDatagram("", "", data="")
        while True:
            try:
                ip_data_packet = self.received_datagram_queue.get()
                ip_data.unpack(ip_data_packet)
                if ip_data.ip_proto == socket.IPPROTO_UDP:
                    self.rip_simulator.received_queue.put(ip_data.data)
                else:
                    LOG.info(self.name + ":from route_ip_datagram+:" + ip_data.__repr__())
                    dest_ip = socket.inet_ntoa(ip_data.ip_dest_addr)
                    LOG.debug(self.name + ":from des_ip+:" + dest_ip)
                    # inter_ip = self.route_table.find_longest_match_network(dest_ip)
                    match_row = self.route_table.find_shortest_path(dest_ip)
                    if match_row:
                        LOG.debug(self.name + ":matched interface IP:" + match_row.inter_ip)
                        for interface in self.intList:
                            if interface.ip_addr != "0.0.0.0" and IPAddress(interface.ip_addr) == \
                                    IPAddress(match_row.inter_ip):
                                LOG.debug("matched interface=" + interface.name)
                                if match_row.metric == 0:
                                    interface.send_queue.put([match_row.dest_ip, ip_data_packet])
                                else:
                                    interface.send_queue.put([match_row.next_ip, ip_data_packet])
                    else:
                        LOG.debug(self.name + ":**** dest ip =" + dest_ip + " not reachable or current router address!!")

            except Empty:
                pass
                # finally:
                #     self.route_ip_datagram()

    def init_arp_mac_table(self):
        self.arp_mac_table.mac_table = []
        for inter in self.intList:
            if inter.ip_addr != "0.0.0.0":
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
