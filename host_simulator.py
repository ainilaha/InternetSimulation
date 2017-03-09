import multiprocessing

import binascii
import os
import socket
import threading

import time
from Queue import Empty

from netaddr import EUI
from netaddr import IPAddress

from arp_mac_table import ARPnMACTable, ARPnMACRow
from ethernet import EthernetFrame
from ip import IPDatagram
from logger import LOG
from rip_packet import RIPPacket
from rip_simulator import RIPSimulator
from router_simulator import Interface
from routing_table import RoutingTable
from udp import UDPPacket


class HostSimulator:
    def __init__(self, name):
        self.intList = []  # there is only on interface in host
        self.name = name
        self.received_frame_data_queue = multiprocessing.Queue()
        self.tcp_ip_queue = multiprocessing.Queue()
        self.chat_window = None
        self.route_table = RoutingTable(router=self)
        self.arp_mac_table = ARPnMACTable()
        self.config_file_path = "config/" + self.name
        self.arp_mac_table_path = "config/" + self.name + "_apr_mac"
        self.ini_interface()
        self.host_receiving = threading.Thread(target=self.receive_datagram)
        self.host_receiving.start()
        self.rip_simulator = RIPSimulator(self)

    def ini_interface(self):
        mac = binascii.b2a_hex(os.urandom(6))  # random generate 48-bit Mac Address presented by 12 hex numbers
        interface = Interface()
        interface.mac = str(EUI(mac))
        interface.router = self
        interface.name = "eth0"
        interface.type = 1
        self.intList.append(interface)
        self.load_config()

    def test_recv(self):
        try:
            # process Ethernet frame
            ip_bytes = self.tcp_ip_queue.get()
            ip_datagram = IPDatagram(ip_dest_addr='',ip_src_addr='')
            ip_datagram.unpack(ip_bytes)

        except Empty:
            pass

    def receive_datagram(self):
        LOG.info(self.name + ":starting listening and routing...")
        time.sleep(0.01)
        data_frame = EthernetFrame(dest_mac="", src_mac="")
        ip_data = IPDatagram("", "", data="")
        while True:
            try:
                ip_data_packet = self.received_frame_data_queue.get()
                data_frame.unpack(ip_data_packet)
                ip_data.unpack(data_frame.data)
                if ip_data.ip_proto == socket.IPPROTO_UDP:
                    udp_packet = UDPPacket()
                    udp_packet.unpack(ip_data.data)
                    rip_packet = RIPPacket(udp_packet)
                    rip_packet.unpack(udp_packet.data)
                    LOG.debug(
                        self.name + ": receive rip packets=" + rip_packet.__repr__())  # go to UDP k.o
                    self.rip_simulator.received_queue.put(ip_data.data)
                elif ip_data.ip_proto == socket.IPPROTO_TCP:
                    # tcp_segment = TCPSegment(ip_src_addr='', ip_dest_addr='', data='')
                    # tcp_segment.unpack(ip_data.data)
                    # if tcp_segment.tcp_fpsh:
                    #     # should use similar _recv from socket to segment
                    #     self.chat_window.queue.put(tcp_segment.data)
                    self.tcp_ip_queue.put(ip_data.pack())
                    LOG.info(self.name + ": receive tcp ip packets=" + ip_data.__repr__())
                else:
                    LOG.info(self.name + ": receive ip packets=" + ip_data.__repr__())  # will print it on chat window
                    self.chat_window.queue.put(ip_data_packet)
            except Empty:
                pass
            finally:
                time.sleep(0.001)

    def send_datagram(self, ip_packets):
        LOG.info(self.name + ":----------------send_datagram------------------------------")
        ip_data = IPDatagram("", "", data="")
        ip_data.unpack(ip_packets)
        LOG.info(self.name + ":from send_datagram+:" + ip_data.__repr__())
        dest_ip = socket.inet_ntoa(ip_data.ip_dest_addr)
        LOG.debug(self.name + ":from des_ip+:" + dest_ip)
        match_row = self.route_table.find_shortest_path(dest_ip)
        if match_row:
            if IPAddress(self.intList[0].ip_addr) == IPAddress(match_row.inter_ip):
                LOG.debug("matched interface=" + self.intList[0].name)
                src_mac = ARPnMACTable.get_mac_pack(self.intList[0].mac)
                ip_frame = EthernetFrame(src_mac, src_mac, tcode=0x0800, data=ip_packets)
                LOG.info(self.name + " :from send_datagram: " + ip_frame.__repr__())
                self.intList[0].send_queue.put([match_row.next_ip, ip_packets])
            else:
                LOG.info(self.name + "from send_datagram:not match routing row")
        else:
            LOG.info(self.name + ":**** dest ip =" + dest_ip + " not reachable or dest ip is current host...")

    def init_arp_mac_table(self):
        self.arp_mac_table.mac_table = []
        arp_n_mac_row = ARPnMACRow(ip_addr=self.intList[0].ip_addr, mac=self.intList[0].mac, mac_type=1,
                                   inter_name=self.intList[0].name, age=-1)
        self.arp_mac_table.mac_table.append(arp_n_mac_row)

    def save_config(self):
        if os.path.exists(self.config_file_path):
            os.remove(self.config_file_path)
        conf_file = open(self.config_file_path, 'a+')  # Trying to create a new file or open one

        conf_file.write(self.intList[0].name + " : " + str(self.intList[0].type) + " : " + self.intList[0].ip_addr +
                        " : " + self.intList[0].mac + os.linesep)
        conf_file.close()
        self.init_arp_mac_table()
        self.arp_mac_table.save_table(self.arp_mac_table_path)

    def load_config(self):
        if os.path.exists(str(self.config_file_path)):
            conf_file = open(self.config_file_path, 'r')
            line = conf_file.read()
            line = line.split(":")
            self.intList[0].name = str(line[0]).strip()
            self.intList[0].type = str(line[1]).strip()
            self.intList[0].ip_addr = str(line[2]).strip()
            self.intList[0].mac = str(line[3]).strip()
            self.arp_mac_table.mac_table = []
            self.arp_mac_table.load_table_config(self.arp_mac_table_path)

    def show_config(self):
        LOG.info(self.intList[0].name + " : " + str(self.intList[0].type) + " : " + self.intList[0].ip_addr + \
                 " : " + self.intList[0].mac + "\n")
        LOG.info("----------------------------------------\n")
