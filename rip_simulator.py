import multiprocessing
import socket
import threading

import time
from Queue import Empty

from rip_packet import Entry, RIPPacket
from routing_table import RoutingRow
from udp import UDPSimulator, UDPPacket

RIP_REFRESH_TIME = 5  # its refresh 30 seconds in real network, I set it as 5 for conventing demo


class RIPSimulator:
    def __init__(self, router=None):
        self.router = router
        self.udp_simulator = UDPSimulator(router=self.router)
        self.received_queue = multiprocessing.Queue()
        self.receiving_rip_udp = threading.Thread(target=self.receive_rip_udp)
        # self.receiving_rip_udp.daemon = True  # should run as daemon
        self.receiving_rip_udp.start()
        self.sending_rip_udp = threading.Thread(target=self.send_rip)
        # self.sending_rip_udp.daemon = True
        self.sending_rip_udp.start()

    def send_rip(self):
        print self.router.name + ":starting sending RIP UDP....."
        while True:
            for inter in self.router.intList:
                rip_packet = RIPPacket()
                for router_row in self.router.route_table.table:
                    dest_ip = socket.inet_aton(router_row.dest_ip)
                    entry = Entry(ip_addr=dest_ip, nex_ip=socket.inet_aton(inter.ip_addr))
                    rip_packet.entry_list.append(entry)
                if len(rip_packet.entry_list) > 0:
                    print self.router.name + " :send_rip: " + rip_packet.__repr__()
                    self.udp_simulator.send_multicast(rip_packet.pack(), inter)
            time.sleep(RIP_REFRESH_TIME)

    def receive_rip_udp(self):
        print self.router.name + ":starting listening and receiving RIP UDP....."
        time.sleep(0.01)
        udp_packet = UDPPacket()
        while True:
            try:
                udp_bits = self.received_queue.get(0)
                udp_packet.unpack(udp_bits)
                print self.router.name + "from receive_udp:" + udp_packet.__repr__()
                self.update_routing_table(udp_bits)
            except Empty:
                pass
            finally:
                time.sleep(0.1)

    def update_routing_table(self, udp_bits):
        udp_packet = UDPPacket()
        udp_packet.unpack(udp_bits)
        rip_packet = RIPPacket()
        rip_packet.unpack(udp_packet.data)
        for entry in rip_packet.entry_list:
            route_row = RoutingRow(dest_ip=entry.ip_addr, next_ip=entry.next_ip, inter_ip=udp_packet.dest_addr)
            self.router.route_table.table.append(route_row)
        print self.router.name + "----routing table updated----------------\n"
        self.router.route_table.show_table()
