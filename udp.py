'''
UDP Field:
 0      7 8     15 16    23 24    31
+--------+--------+--------+--------+
|      Source     |    Destination  |
|       Port      |       Port      |
+--------+--------+--------+--------+
|      Length     |     Checksum    |
+--------+--------+--------+--------+
|
|        data octets ...
'''
import socket

from struct import pack, unpack, calcsize

from netaddr import IPAddress
from netaddr import IPNetwork

from ip import IPDatagram
from logger import LOG

UDP_HDR_FMT = '!II4s4s'


class UDPPacket:
    def __init__(self, src_addr='', dest_addr='', data=''):
        self.src_addr = src_addr
        self.dest_addr = dest_addr
        self.data = data
        self.checksum = 0
        self.length = calcsize(UDP_HDR_FMT) + len(
            self.data)  # length specifies the length in bytes of the UDP header and UDP data

    def __repr__(self):
        rep = 'UDPPacket: [ src_addr:%s, dest_addr:%s, length:%d, checksum:%d]' \
              % (socket.inet_ntoa(self.src_addr), socket.inet_ntoa(self.dest_addr), self.length,
                 self.checksum)
        return rep

    def pack(self):
        self.length = calcsize(UDP_HDR_FMT) + len(self.data)
        udp_head = pack(UDP_HDR_FMT, self.length, self.checksum, self.src_addr, self.dest_addr)
        udp_packed = ''.join([udp_head, self.data])
        return udp_packed

    def unpack(self, udp_datagram):
        udp_fields = unpack(UDP_HDR_FMT, udp_datagram[:calcsize(UDP_HDR_FMT)])
        self.length = udp_fields[0]
        self.checksum = udp_fields[1]
        self.src_addr = udp_fields[2]
        self.dest_addr = udp_fields[3]
        self.data = udp_datagram[calcsize(UDP_HDR_FMT):self.length]


class UDPSimulator:
    def __init__(self, router=None):
        self.router = router

    def send_multicast(self, rip_packet, interface):
        local_network_id = IPNetwork(interface.ip_addr + "/" + interface.net_mask).cidr
        for router in self.router.route_table.host_list + self.router.route_table.router_list:
            if router != self.router:
                for inter in router.intList:
                    if IPAddress(inter.ip_addr) in local_network_id and inter.ip_addr != interface.ip_addr:
                        udp_packet = UDPPacket(src_addr=socket.inet_aton(interface.ip_addr),
                                               dest_addr=socket.inet_aton(inter.ip_addr), data=rip_packet.pack())
                        ip_data = IPDatagram(ip_src_addr=socket.inet_aton(interface.ip_addr),
                                             ip_dest_addr=socket.inet_aton(inter.ip_addr),
                                             ip_proto=socket.IPPROTO_UDP,
                                             data=udp_packet.pack())
                        # print self.router.name + "send_multicast:" + ip_data.__repr__()
                        LOG.debug(self.router.name + "udp RIP sender interface:" + interface.ip_addr +
                                  "dest_ip=" + inter.ip_addr+"rip_data="+rip_packet.__repr__())
                        interface.send_queue.put([inter.ip_addr, ip_data.pack()])


if __name__ == '__main__':
    src_ip = socket.inet_aton("192.168.1.1")
    dest_ip = socket.inet_aton("192.100.1.1")
    udp = UDPPacket(src_addr=src_ip, dest_addr=dest_ip)
    print "udp1=" + udp.__repr__()
    udp2 = UDPPacket()
    udp2.unpack(udp.pack())
    print "udp2=" + udp2.__repr__()
