import socket
from struct import pack, unpack, calcsize

RIP_HDR_FMT = '!BB'
RIP_ENTRY_FMT = '!BH4s4s'


class Entry:
    def __init__(self, afi=2, ip_addr='', nex_ip='', metric=0):
        self.afi = afi  # Set to a value of 2 for IP
        self.ip_addr = ip_addr
        self.next_ip = nex_ip  # it is more like feature of RIPv2
        self.metric = metric  # measure by hops in RIP

    def __repr__(self):
        rep = 'Entry: [ afi:%d, addr:%s, next_ip:%s, metric:%d]' \
              % (self.afi, socket.inet_ntoa(self.ip_addr), socket.inet_ntoa(self.next_ip), self.metric)
        return rep

    def pack(self):
        rip_packet = pack(RIP_ENTRY_FMT, self.afi, self.metric, self.ip_addr, self.next_ip)
        return rip_packet

    def unpack(self, entry):
        rip_fields = unpack(RIP_ENTRY_FMT, entry[:calcsize(RIP_ENTRY_FMT)])
        self.afi = rip_fields[0]
        self.metric = rip_fields[1]
        self.ip_addr = rip_fields[2]
        self.next_ip = rip_fields[3]


class RIPPacket:
    def __init__(self, cmd=0, ver=1):
        # RIP head:
        self.cmd = cmd  # request or response
        self.ver = ver
        # RIP data:
        self.entry_list = []

    def __repr__(self):
        rep = 'RIPPacket: [cmd:%s, ver:%d] entry data' \
              % ('request' if self.cmd == 0 else "response", self.ver)
        for entry in self.entry_list:
            rep = rep + ":" + entry.__repr__()
        return rep

    def pack(self):
        rip_packet = pack(RIP_HDR_FMT, self.cmd, self.ver)
        entry_pack = b''
        for entry in self.entry_list:
            entry_pack = entry_pack + entry.pack()
        return rip_packet + entry_pack

    def unpack(self, rip_packet):
        # unpack head
        rip_fields = unpack(RIP_HDR_FMT, rip_packet[:calcsize(RIP_HDR_FMT)])
        self.cmd = rip_fields[0]
        self.ver = rip_fields[1]
        # unpack entry list
        entry_list = rip_packet[calcsize(RIP_HDR_FMT):]
        entry = Entry()
        while len(entry_list) > 0 and len(entry_list) % calcsize(RIP_ENTRY_FMT) == 0:
            entry_packed = entry_list[:calcsize(RIP_ENTRY_FMT)]
            entry_list = entry_list[calcsize(RIP_ENTRY_FMT):]
            entry.unpack(entry_packed)
            self.entry_list.append(entry)


def main():
    ip = "10.10.10.11"
    ip_p = socket.inet_aton(ip)
    ip2 = "10.10.10.12"
    ip_p2 = socket.inet_aton(ip2)
    entry = Entry(ip_addr=ip_p,nex_ip=ip_p2)
    print "entry1=" + entry.__repr__()
    entry2 = Entry(ip_addr=ip_p, nex_ip=ip_p2)
    print entry2.unpack(entry.pack())
    print "entry2=" + entry.__repr__()
    rip = RIPPacket(cmd=0)
    rip.entry_list.append(entry)
    rip.entry_list.append(entry2)

    print "rip1=" + rip.__repr__()
    rip2 = RIPPacket(cmd=0)
    rip2.unpack(rip.pack())
    print "rip2=" + rip2.__repr__()


if __name__ == "__main__":
    main()
