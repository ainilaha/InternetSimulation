'''
This is simple model of routing table.
according to https://en.wikipedia.org/wiki/Routing_table

IPv4 Route Table
===========================================================================
Active Routes:
Network Destination        Netmask          Gateway       Interface  Metric
          0.0.0.0          0.0.0.0      192.168.1.1    192.168.1.104     25
      192.168.1.0    255.255.255.0         On-link     192.168.1.104    281
    192.168.1.104  255.255.255.255         On-link     192.168.1.104    281
    192.168.1.255  255.255.255.255         On-link     192.168.1.104    281
        224.0.0.0        240.0.0.0         On-link     192.168.1.104    281
  255.255.255.255  255.255.255.255         On-link     192.168.1.104    281
===========================================================================
'''
from netaddr import IPAddress
from netaddr import IPNetwork


class RoutingRow:
    def __init__(self, int_ip, mask="255.255.255.0"):
        self.destination = ""
        self.net_mask = mask
        self.gateway = "0.0.0.0"
        self.interface = int_ip  # an ip address or name of interface
        self.matrix = 0  # hops


class RoutingTable:
    def __init__(self):
        self.table = []

    @staticmethod
    def get_network_id(routing_row):
        return IPNetwork(routing_row.interface + "/" + routing_row.net_mask).cidr

    '''
     This method will return the longest match network interface.
     Note: it possible has more than one longest match network interface in real case bu here I keep it for simple
     and just return one of the longest match network interface if it has more than one.
    '''

    def find_longest_match_network(self, ip_address):
        ip_address = IPAddress(ip_address)
        match_interface_list = []
        for routing_row in self.table:
            network_id = self.get_network_id(routing_row)
            if ip_address in network_id:
                match_interface_list.append(routing_row)
        common_bits = [(IPAddress(self.get_network_id(routing_row)) &
                        ip_address).bits() for routing_row in match_interface_list]
        common_bit_counts = [bits.count('1') for bits in common_bits]
        max_index = common_bit_counts.index(6)
        return match_interface_list[max_index]


if __name__ == "__main__":
    rt1 = RoutingRow("10.10.10.9", "255.255.252.0")
    rt2 = RoutingRow("10.10.10.11", "255.255.255.0")
    print RoutingTable.get_network_id(rt1)
    print RoutingTable.get_network_id(rt2)
    rb = RoutingTable()
    rb.table.append(rt1)
    rb.table.append(rt2)
    print "longest match:", rb.find_longest_match_network("10.10.10.10").interface
