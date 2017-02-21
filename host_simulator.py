import multiprocessing

import binascii
import os
import threading

import time
from Queue import Empty

from netaddr import EUI

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
        self.ini_interface()
        self.chat_window = None
        self.route_table = RoutingTable()
        self.arp_mac_table = ARPnMACTable()
        self.config_file_path = "config/" + self.name
        self.arp_mac_table_path = "config/" + self.name + "_apr_mac"
        self.host_receiving = threading.Thread(target=self.receive_datagram)
        self.host_receiving.start()

    def ini_interface(self):
        mac = binascii.b2a_hex(os.urandom(6))  # random generate 48-bit Mac Address presented by 12 hex numbers
        self.interface = Interface()
        self.interface.mac = str(EUI(mac))
        self.interface.router = self
        self.interface.name = "eth0"
        self.interface.type = 1

    def receive_datagram(self):
        print self.name + ":starting listening and routing..."
        time.sleep(0.01)
        data_frame = EthernetFrame(dest_mac="", src_mac="")
        ip_data = IPDatagram("", "", data="")
        while True:
            try:
                ip_data_packet = self.received_frame_data_queue.get()
                data_frame.unpack(ip_data_packet)
                ip_data.unpack(data_frame.unpack())
                print self.name + ": receive ip packets="+ip_data.__repr__() # will print it on chat window
            except Empty:
                pass
            finally:
                time.sleep(0.001)

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
        print self.interface.name + " : " + str(self.interface.type) + " : " + self.interface.ip_addr +\
              " : " + self.interface.mac + "\n"
        print "----------------------------------------\n"

    def send_datagram(self, ip_packet):
        self.interface.send_queue.put(ip_packet)