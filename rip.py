# should run as daemon
import socket
from struct import pack, unpack, calcsize

RIP_HDR_FMT = '!BBBH4s'


class RIPPacket:
    def __init__(self, cmd=0, ver=1, afi=2, ip_addr='', metric=0):
        # RIP head:
        self.cmd = cmd  # request or response
        self.ver = ver
        # RIP data:
        self.afi = afi  # Set to a value of 2 for IP
        self.ip_addr = ip_addr
        self.metric = metric

    def __repr__(self):
        rep = 'RIPPacket: [cmd:%s, ver:%d, afi:%d, addr:%s, metric:%d]' \
              % ('request' if self.cmd == 0 else "response", self.ver, self.afi,
                 socket.inet_ntoa(self.ip_addr), self.metric)
        return rep

    def pack(self):
        rip_packet = pack(RIP_HDR_FMT,
                          self.cmd, self.ver, self.afi, self.metric, self.ip_addr)
        return rip_packet

    def unpack(self, rip_packet):
        rip_fields = unpack(RIP_HDR_FMT, rip_packet[:calcsize(RIP_HDR_FMT)])
        self.cmd = rip_fields[0]
        self.ver = rip_fields[1]
        self.afi = rip_fields[2]
        self.metric = rip_fields[3]
        self.ip_addr = rip_fields[4]


def main():
    ip = "10.10.10.11"
    ip_p = socket.inet_aton(ip)
    rip = RIPPacket(cmd=0, ip_addr=ip_p)
    print "rip1=" + rip.__repr__()
    rip2 = RIPPacket(cmd=0, ip_addr="")
    rip2.unpack(rip.pack())
    print "rip2=" + rip2.__repr__()


if __name__ == "__main__":
    main()
