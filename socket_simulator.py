import multiprocessing
import struct
from Queue import Empty

from arp import ARPPacket
from ethernet import EthernetFrame
from router_simulator import RouterSimulator


class SocketSimulator:
    def __init__(self, interface=RouterSimulator()):
        self.logger = None
        self.ip_gateway = ""
        self.ip_src = ""
        self.mac_src = ""
        self.host = interface
        self.arp_queue = multiprocessing.Queue()

    '''
    Query the gateway MAC address through ARP request
    '''

    def _get_gateway_mac(self):
        spa = self.ip_src
        sha = self.mac_src
        tpa = self.ip_gateway
        # pack the ARP broadcast mac address
        tha = struct.pack('!6B',
                          int('FF', 16), int('FF', 16), int('FF', 16),
                          int('FF', 16), int('FF', 16), int('FF', 16))
        # pack ARP request
        arp_packet = ARPPacket(sha=sha, spa=spa, tha=tha, tpa=tpa)
        eth_data = arp_packet.pack()
        # pack Ethernet Frame: 0x0806 wrapping ARP packet
        eth_frame = EthernetFrame(dest_mac=tha, src_mac=sha, tcode=0x0806, data=eth_data)
        self.logger.debug('Sending ARP REQUEST for the gateway MAC:' +
                          '\n\t%s\n\t%s' % (arp_packet, eth_frame))
        self.logger.info('Querying gateway MAC address, %s' % arp_packet)
        phy_data = eth_frame.pack()
        self.send(phy_data)

        while True:
            try:
                packet = self.arp_queue.get(0)
                eth_frame.unpack(packet)
                if eth_frame.eth_tcode == 0x0806:
                    break
            except Empty:
                pass
        arp_packet.unpack(eth_frame.data)
        self.logger.debug('Receiving ARP REPLY of the gateway MAC:' +
                          '\n\t%s\n\t%s' % (arp_packet, eth_frame))
        self.logger.info('Get gateway MAC address, %s' % arp_packet)
        return arp_packet.arp_sha

    # send ARP request
    def send_arp(self, packet):
        print "send according destination address of " + packet
        for interface in self.host.intList:
            interface.receive_queue.put(packet)
