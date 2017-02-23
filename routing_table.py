'''
This is simple model of routing table.
according to https://en.wikipedia.org/wiki/Routing_table

IPv4 Route Table
===========================================================================
Active Routes:
Network Destination        Netmask          Gateway/next_ip       Interface  Metric
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
    def __init__(self, dest_ip, next_ip, inter_ip, net_mask="255.255.255.0"):
        self.dest_ip = dest_ip
        self.net_mask = net_mask
        self.next_ip = next_ip  # next hop ( or gateway) IP or connected status (on-link)
        self.inter_ip = inter_ip  # an ip address or name of interface
        self.hops = 0  # hops


class RoutingTable:
    def __init__(self):
        self.table = []
        self.router_list = []

    @staticmethod
    def get_network_id(routing_row):
        return IPNetwork(routing_row.dest_ip + "/" + routing_row.net_mask).cidr

    def show_table(self):
        print "--------------------------routing table-------------------------------------"
        for router_row in self.table:
            print router_row.dest_ip + " : " + router_row.next_ip + " : " + router_row.net_mask + " : " +\
                  router_row.inter_ip

    def update_table(self, route_row):
        self.table.append(route_row)

    def init_routing_table(self, router):
        '''
        This method will learn from all other routers and learn connected rows
        :param router: current router
        :return:
        '''
        for other_router in self.router_list:
            if other_router != router:
                for inter in router.intList:
                    for other_inter in other_router.intList:
                        if IPNetwork(inter.ip_addr + "/" + inter.net_mask) == \
                                IPNetwork(other_inter.ip_addr + "/" + other_inter.net_mask):
                            routing_row = RoutingRow(dest_ip=other_inter.ip_addr, next_ip=other_inter.ip_addr,
                                                     inter_ip=inter.ip_addr, net_mask=inter.net_mask)
                            self.table.append(routing_row)

    def find_shortest_path(self, dest_ip):
        match_rows = []
        for routing_row in self.table:
            if IPAddress(dest_ip) in self.get_network_id(routing_row):
                if IPAddress(routing_row.next_ip.strip()) == IPAddress(dest_ip):  # send the data frame if its connected
                    return routing_row
                else:
                    match_rows.append(routing_row)
        longest_match_list = self.find_longest_match_network(dest_ip, match_rows)
        if len(longest_match_list) == 1:
            return longest_match_list[0]
        elif len(longest_match_list) > 1:
            # find the shortest path if there are more than one paths to routing
            hops_list = [routing_row.hops for routing_row in match_rows]
            min_index = hops_list.index(min(hops_list))
            return match_rows[min_index]
        else:
            return None

    def find_longest_match_network(self, ip_address, match_interface_list):
        '''
         This method will return the longest match network interface.
         Note: it possible has more than one longest match network interface in real case
        '''
        ip_address = IPAddress(ip_address)
        common_bits = [(IPAddress(self.get_network_id(routing_row)) &
                        ip_address).bits() for routing_row in match_interface_list]
        common_bit_counts = [bits.count('1') for bits in common_bits]
        if len(common_bit_counts) > 0:
            max_value = max(common_bit_counts)
            print "max_value=" + str(max_value)
            max_index_list = [i for i, value in enumerate(common_bit_counts) if value == max_value]
            print "max_index=" + str(max_index_list)
            return [match_interface_list[index] for index in max_index_list]
        else:
            return []


if __name__ == "__main__":
    # rt1 = RoutingRow("10.10.10.9", "10.10.10.11",)
    # rt2 = RoutingRow("10.10.10.11", "10.10.10.10")

    # rb = RoutingTable()
    # rb.table.append(rt1)
    # rb.table.append(rt2)
    # print "longest match:", rb.find_longest_match_network("10.10.10.10")
    if IPNetwork("192.168.1.20/255.255.255.0") == IPNetwork("192.168.1.3/255.255.255.0"):
        print IPNetwork("192.168.1.20/255.255.255.0")
