import multiprocessing
import socket
import threading

import time
from Queue import Empty

from logger import LOG
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
        self.receiving_rip_udp.daemon = True  # should run as daemon
        self.receiving_rip_udp.start()
        self.sending_rip_udp = threading.Thread(target=self.send_rip)
        self.sending_rip_udp.daemon = True
        self.sending_rip_udp.start()

    def send_rip(self):
        LOG.info(self.router.name + ":starting sending RIP UDP.....")
        while True:
            for inter in self.router.intList:
                rip_packet = RIPPacket()
                for router_row in self.router.route_table.table:
                    dest_ip = socket.inet_aton(router_row.dest_ip)
                    if router_row.inter_ip != inter.ip_addr:  # horizontal split
                        entry = Entry(ip_addr=dest_ip, nex_ip=socket.inet_aton(inter.ip_addr), metric=router_row.metric)
                        if entry.__repr__() not in [ent.__repr__() for ent in rip_packet.entry_list]:
                            rip_packet.entry_list.append(entry)
                if len(rip_packet.entry_list) > 0:
                    LOG.debug(self.router.name + "inter:"+inter.ip_addr + "*************send table:" + rip_packet.__repr__())
                    self.udp_simulator.send_multicast(rip_packet, inter)

            time.sleep(RIP_REFRESH_TIME)

    def receive_rip_udp(self):
        LOG.info(self.router.name + ":starting listening and receiving RIP UDP.....")
        time.sleep(0.01)
        udp_packet = UDPPacket()
        while True:
            try:
                udp_bits = self.received_queue.get(0)
                udp_packet.unpack(udp_bits)
                rip_packet = RIPPacket(udp_packet.data)
                LOG.debug(self.router.name + "from receive_udp:" + udp_packet.__repr__() + "..." + rip_packet.__repr__())
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
            if socket.inet_ntoa(entry.ip_addr) != socket.inet_ntoa(udp_packet.dest_addr):
                LOG.debug(self.router.name + "received table" + rip_packet.__repr__())
                route_row = RoutingRow(dest_ip=socket.inet_ntoa(entry.ip_addr), next_ip=socket.inet_ntoa(entry.next_ip),
                                       inter_ip=socket.inet_ntoa(udp_packet.dest_addr), metric=entry.metric)
                self.router.route_table.update_table(route_row)
            else:
                LOG.debug("****rip:update_routing_table***********dest:%s******next_ip:%s********************" %
                          (socket.inet_ntoa(entry.ip_addr),socket.inet_ntoa(udp_packet.dest_addr)))
            # self.router.route_table.show_table()
