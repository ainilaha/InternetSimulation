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
from router_simulator import Interface
from routing_table import RoutingTable


class HostSimulator:
    def __init__(self, name):
        self.interface = None
        self.name = name
        self.received_frame_data_queue = multiprocessing.Queue()
        self.chat_window = None
        self.route_table = RoutingTable()
        self.arp_mac_table = ARPnMACTable()
        self.config_file_path = "config/" + self.name
        self.arp_mac_table_path = "config/" + self.name + "_apr_mac"
        self.ini_interface()
        self.host_receiving = threading.Thread(target=self.receive_datagram)
        self.host_receiving.start()

    def ini_interface(self):
        mac = binascii.b2a_hex(os.urandom(6))  # random generate 48-bit Mac Address presented by 12 hex numbers
        self.interface = Interface()
        self.interface.mac = str(EUI(mac))
        self.interface.router = self
        self.interface.name = "eth0"
        self.interface.type = 1
        self.load_config()

    def receive_datagram(self):
        print self.name + ":starting listening and routing..."
        time.sleep(0.01)
        data_frame = EthernetFrame(dest_mac="", src_mac="")
        ip_data = IPDatagram("", "", data="")
        while True:
            try:
                ip_data_packet = self.received_frame_data_queue.get()
                data_frame.unpack(ip_data_packet)
                ip_data.unpack(data_frame.data)
                print self.name + ": receive ip packets=" + ip_data.__repr__()  # will print it on chat window
            except Empty:
                pass
            finally:
                time.sleep(0.001)

    def send_datagram(self, ip_packets):
        print "----------------send_datagram------------------------------"
        ip_data = IPDatagram("", "", data="")
        ip_data.unpack(ip_packets)
        print self.name + ":from send_datagram+:" + ip_data.__repr__()
        dest_ip = socket.inet_ntoa(ip_data.ip_dest_addr)
        print self.name + ":from des_ip+:" + dest_ip
        match_row = self.route_table.find_shortest_path(dest_ip)
        if match_row:
            print "---------send_datagram--------------if"
            if IPAddress(self.interface.ip_addr) == IPAddress(match_row.inter_ip):
                print "matched interface=" + self.interface.name
                src_mac = ARPnMACTable.get_mac_pack(self.interface.mac)
                ip_frame = EthernetFrame(src_mac, src_mac, tcode=0x0800, data=ip_packets)
                print self.name + " :from send_datagram: " + ip_frame.__repr__()
                self.interface.send_queue.put([match_row.next_ip,ip_packets])
            else:
                print "not match"
        else:
            print "-----------send_datagram------------else"
            print self.name + ":**** dest ip =" + dest_ip + " not reachable or dest ip is current host..."

    def init_arp_mac_table(self):
        self.arp_mac_table.mac_table = []
        arp_n_mac_row = ARPnMACRow(ip_addr=self.interface.ip_addr, mac=self.interface.mac, mac_type=1,
                                   inter_name=self.interface.name, age=-1)
        self.arp_mac_table.mac_table.append(arp_n_mac_row)

    def save_config(self):
        if os.path.exists(self.config_file_path):
            os.remove(self.config_file_path)
        conf_file = open(self.config_file_path, 'a+')  # Trying to create a new file or open one

        conf_file.write(self.interface.name + " : " + str(self.interface.type) + " : " + self.interface.ip_addr +
                        " : " + self.interface.mac + os.linesep)
        conf_file.close()
        self.init_arp_mac_table()
        self.arp_mac_table.save_table(self.arp_mac_table_path)

    def load_config(self):
        if os.path.exists(str(self.config_file_path)):
            conf_file = open(self.config_file_path, 'r')
            line = conf_file.read()
            line = line.split(":")
            self.interface.name = str(line[0]).strip()
            self.interface.type = str(line[1]).strip()
            self.interface.ip_addr = str(line[2]).strip()
            self.interface.mac = str(line[3]).strip()
            self.arp_mac_table.mac_table = []
            self.arp_mac_table.load_table_config(self.arp_mac_table_path)

    def show_config(self):
        print self.interface.name + " : " + str(self.interface.type) + " : " + self.interface.ip_addr + \
              " : " + self.interface.mac + "\n"
        print "----------------------------------------\n"

