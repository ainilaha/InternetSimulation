import multiprocessing
import socket
import threading

import time

import struct
from Queue import Empty

from enum import Enum
from netaddr import EUI

from arp import ARPPacket
from arp_mac_table import ARPnMACTable
from ethernet import EthernetFrame
from ip import IPDatagram
from logger import LOG


class State(Enum):
    BESSY = 0
    AVAIlIBBIE = 1
    NO_CONNECTED = 2


'''
Interface class simulated an interface of a router. Each interface hold a send out queue to address packets.
However, there is no receive queue in an interface since all received packets will go to the total queue
in the router.
Note: Here I am using a state control variable to simulated an interface interrupt in real OS

'''


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
            LOG.debug(self.router.name + ":" + self.name + ":interface starting send frame.....")
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
                if inter.ip_addr != "0.0.0.0":
                    inter.received_frame_queue.put(eth_frame)
        for host in self.router.arp_mac_table.host_list:
            if host.intList[0].ip_addr != "0.0.0.0":
                host.intList[0].received_frame_queue.put(eth_frame)

    def send_packet(self, next_ip_n_packets):

        if len(next_ip_n_packets) == 2:
            ip_data = IPDatagram("", "", data="")
            ip_data.unpack(next_ip_n_packets[1])
            next_ip = next_ip_n_packets[0]
            # print self.router.name + ":" + self.name + " : send_packet1 " + ip_data.__repr__()
            dest_mac_row = self.router.arp_mac_table.get_mac_from_table(next_ip)
            if dest_mac_row:
                LOG.debug("-----------if-------send_frame--" + self.mac + "-------------------" + dest_mac_row.mac)
                eth_frame = EthernetFrame(src_mac=ARPnMACTable.get_mac_pack(self.mac),
                                          dest_mac=ARPnMACTable.get_mac_pack(dest_mac_row.mac),
                                          data=ip_data.pack())
                LOG.debug(self.router.name + ":" + self.name + " : send_packet2 " + eth_frame.__repr__())
                self.send_frame(eth_frame.pack())
            else:
                LOG.debug("-----------else-------send_frame----------------------")
                dest_mac = self.send_arp_request(next_ip)
                eth_frame = EthernetFrame(src_mac=ARPnMACTable.get_mac_pack(self.mac),
                                          dest_mac=dest_mac, data=next_ip_n_packets[1])
                LOG.debug(self.router.name + ":" + self.name + " : else eth" + eth_frame.__repr__())
                LOG.debug(self.router.name + ":" + self.name + " : else send_packet: " + ip_data.__repr__())
                self.send_frame(eth_frame.pack())
                LOG.debug(self.router.name + " : " + self.name + " : " + "update_mac_table:" + EthernetFrame.eth_addr(
                    dest_mac))
                self.router.arp_mac_table.update_mac(EthernetFrame.eth_addr(dest_mac), ip_data.ip_dest_addr, self.name)
                self.send_packet(ip_data.pack())

    def receive_frame(self):
        LOG.debug(self.name + ":starting listening and receiving frame.....")
        time.sleep(0.01)
        data_frame = EthernetFrame(dest_mac="", src_mac="")
        while True:
            try:
                ip_data_frame = self.received_frame_queue.get()
                data_frame.unpack(ip_data_frame)
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
        LOG.debug("-----------------------send_arp_request---------------------------")
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
        # print self.router.name + " : " + self.name + ":send_arp_request:" + eth_frame.__repr__()
        # print self.router.name + " : " + self.name + ":send_arp_request++:" + arp_packet.__repr__()
        phy_data = eth_frame.pack()

        for router in self.router.arp_mac_table.router_list:
            for inter in router.intList:
                if inter.ip_addr != "0.0.0.0":
                    inter.received_frame_queue.put(phy_data)
        for host in self.router.arp_mac_table.host_list:
            if host.intList[0].ip_addr != "0.0.0.0":
                host.intList[0].received_frame_queue.put(phy_data)
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
        LOG.debug(self.name + ":Listening ARP.... ")
        arp_frame = EthernetFrame(dest_mac="", src_mac="")
        arp_frame.unpack(eth_frame)
        arp_packet = ARPPacket(sha="", tha="", spa="")
        LOG.debug(self.name + ":request reply =" + arp_frame.__repr__())
        arp_packet.unpack(arp_frame.data)
        # print self.router.name +":" + self.name+":arp="+ arp_packet.__repr__() + "\n\n"
        # print self.name + ":+++++ =" + str(socket.inet_ntoa(arp_packet.arp_tpa)).strip() +":"+self.ip_addr.strip()
        if str(socket.inet_ntoa(arp_packet.arp_tpa)).strip() == self.ip_addr.strip():
            arp_packet.arp_sha = ARPnMACTable.get_mac_pack(self.mac)
            arp_packet.arp_optr = 0
            arp_frame = EthernetFrame(dest_mac=arp_frame.eth_src_addr,
                                      src_mac=ARPnMACTable.get_mac_pack(self.mac), tcode=0x0806, data=arp_packet.pack())
            # print self.name + "matched and reply arp==" + arp_frame.__repr__()
            # print self.name + "matched and reply arp==" + arp_packet.__repr__()
            self.send_frame(arp_frame.pack())


def main():
    test_mac = struct.pack('!6B',
                           int('7b', 16), int('4c', 16), int('95', 16),
                           int('23', 16), int('e8', 16), int('89', 16))
    print test_mac
    e = EthernetFrame(test_mac, test_mac, data="test data Frame")
    inter = Interface()
    inter.received_frame_queue.put(e.pack())


if __name__ == "__main__":
    main()
