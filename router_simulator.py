import multiprocessing
import os
import binascii
import threading
import time
from multiprocessing import Process

import struct
from enum import Enum
from Queue import Empty

from netaddr import EUI
from netaddr import IPAddress

from arp import ARPPacket
from ethernet import EthernetFrame

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
        self.IP = "0.0.0.0"
        self.STATE = State.AVAIlIBBIE
        self.send_queue = multiprocessing.Queue()
        self.receive_queue = multiprocessing.Queue()

    # this method will convert Mac address to convention format eg
    # eg ec-17-2f-47-82-6c
    @staticmethod
    def insert_dash(string):
        index = 2
        while index < 15:
            string = string[:index] + '-' + string[index:]
            index += 3
        return string

    def set_mac(self, string):
        self.mac = self.insert_dash(string)

    def send(self, tcode=0x0806):
        while True:
            time.sleep(0.001)
            try:
                packet = self.send_queue.get(0)
                print "call ARP or IP and send packets out" + packet
            except Empty:
                pass


'''
RouterSimulator class simulated an Router in simple way.

'''


class RouterSimulator(Process):
    def __init__(self, name):
        self.intList = []
        self.name = name
        self.initialize_router()
        self.message_content = ""
        self.chat_window = None
        self.route_table = []
        self.mac_table = []
        self.initialize_router()
        self.process_manager = multiprocessing.Manager()
        self.received_packets_data_queue = self.process_manager.Queue()
        self.received_frame_data_queue = self.process_manager.Queue()
        self.pool = multiprocessing.Pool()
        # self.arp = self.pool.apply_async(self.reply_arp, ())  # start arp request listening
        self.t = threading.Thread(target=self.reply_arp)
        self.t.start()

    def initialize_router(self):
        int_name_list = "faster 0/0", "faster 1/1", "ser 0/0", "ser 0/1"
        int_type_list = (1, 1, 0, 0)
        for i in range(0, 4):  # each router equiped with four ports
            mac = binascii.b2a_hex(os.urandom(6))  # random generate 48-bit Mac Address presented by 12 hex numbers
            interface = Interface()
            interface.set_mac(mac)
            interface.name = int_name_list[i]
            interface.type = int_type_list[i]
            self.intList.append(interface)

    # def sub_network(self):
    def save_config(self):
        config_file = "config/" + self.name
        if os.path.exists(config_file):
            os.remove(config_file)
        conf_file = open(config_file, 'a+')  # Trying to create a new file or open one
        for port in self.intList:
            conf_file.write(port.name + " : " + str(port.type) + " : " + port.IP + " : " + port.mac + "\n")
        conf_file.close()

    def show_config(self):
        for port in self.intList:
            print port.name + " : " + str(port.type) + " : " + port.IP + " : " + port.mac + "\n"
            print "----------------------------------------\n"

    def reply_arp(self):
        print "Listening ARP.... "
        time.sleep(1)
        arp_frame = EthernetFrame(dest_mac="", src_mac="")
        while True:
            try:
                arp_frame_raw = self.received_frame_data_queue.get(0)
                arp_frame.unpack(arp_frame_raw)
                print "from func:"+arp_frame.__repr__()
                arp_packet = arp_frame.data
                for inter in self.intList:
                    if IPAddress(arp_packet.tha) == IPAddress(inter.IP):
                        arp_packet.arp_sha = inter.mac
                        for mac_row in self.mac_table:
                            if EUI(mac_row.mac) == EUI(arp_frame.eth_src_addr):
                                mac_row.interface.receive_queue.put(arp_packet)
            except Empty:
                pass
            finally:
                self.reply_arp()


def message_port(self, conn):
    conn.send(self.name + ":" + self.message_content)
    message = conn.recv()
    print message + "\n"
    conn.close()
    return message


def main():
    test_mac = struct.pack('!6B',
                           int('7b', 16), int('4c', 16), int('95', 16),
                           int('23', 16), int('e8', 16), int('89', 16))
    tha = struct.pack('!6B',
                      int('FF', 16), int('FF', 16), int('FF', 16),
                      int('FF', 16), int('FF', 16), int('FF', 16))
    ip = struct.pack('4B', 101, 104, 10, 10)

    router = RouterSimulator("Router")
    arp_packet = ARPPacket(sha=test_mac, tha=tha, spa=ip)
    e = EthernetFrame(test_mac, test_mac,tcode=0x0806,data=arp_packet.pack())
    print e.__repr__()
    router.received_frame_data_queue.put(e.pack())
    print "dddddddddddddddddddd"
    router.t.join()


if __name__ == "__main__":
    main()
