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
import os

from netaddr import IPAddress
from netaddr import IPNetwork

from logger import LOG
from utils import delete_entry, DeleteEntryTimer, entry_time_reset

ENTRY_EXPIRE_TIME = 30 * 60  # 30 minutes


class RoutingRow:
    def __init__(self, dest_ip, next_ip, inter_ip, net_mask="255.255.255.0", metric=0, time=-1):
        self.dest_ip = dest_ip
        self.net_mask = net_mask
        self.next_ip = next_ip  # next hop ( or gateway) IP or connected status (on-link)
        self.inter_ip = inter_ip  # an ip address or name of interface
        self.metric = metric  # hops in RIP
        self.time = time  # static routing row is -1 and will not delete from a router and dynamic router will expire

    def __repr__(self):
        return "dest ip:" + self.dest_ip + ", next_ip: " + self.next_ip + ", net mask: " + \
               self.net_mask + ", inter: " + self.inter_ip


class RoutingTable:
    def __init__(self, router=None):
        self.table = []
        self.router_list = []
        self.host_list = []
        self.router = router
        self.timer_list = []

    @staticmethod
    def get_network_id(routing_row):
        return IPNetwork(routing_row.dest_ip + "/" + routing_row.net_mask).cidr

    def show_table(self):
        LOG.info("----------%s--------------routing table-------------------------------------" % self.router.name)
        for router_row in self.table:
            LOG.info("dest ip:" + router_row.dest_ip + ", next_ip: " + router_row.next_ip + ", net mask: " +
                     router_row.net_mask + ", inter: " + router_row.inter_ip + " ,metric: " + str(router_row.metric))

    def update_table(self, route_row):
        if route_row.__repr__() in [route_row_exist.__repr__() for route_row_exist in self.table]:
            LOG.debug("re-setting time+++++++++++++++++++++++++++++++++++++++++++++++++++++" + route_row.__repr__())
            entry_time_reset(self.timer_list, route_row)
        # discard the entry if destination address equal to local address to prevent routing loop
        # elif route_row.dest_ip not in [inter.ip_addr for inter in self.router.intList]:
        else:
            route_row.metric += 1
            self.table.append(route_row)
            entry_timer = DeleteEntryTimer(ENTRY_EXPIRE_TIME, delete_entry, self.table, route_row)
            entry_timer.start()
            self.timer_list.append(entry_timer)
            # self.show_table()

    def init_update_row(self, other_router, inter):
        local_net_id = IPNetwork(inter.ip_addr + "/" + inter.net_mask)
        for other_inter in other_router.intList:
            if other_inter.ip_addr != "0.0.0.0":
                other_net_id = IPNetwork(other_inter.ip_addr + "/" + other_inter.net_mask)
                if other_net_id == local_net_id and (
                        inter.ip_addr != other_inter.ip_addr or other_router == self.router):
                    routing_row = RoutingRow(dest_ip=other_inter.ip_addr, next_ip=inter.ip_addr,
                                             inter_ip=inter.ip_addr, net_mask=inter.net_mask)
                    self.table.append(routing_row)

    def init_routing_table(self, router):
        '''
        This method will learn from all other routers and learn connected rows
        :param router: current router
        :return:
        '''
        # for other_router in self.router_list:
        #     for inter in router.intList:
        #         self.init_update_row(other_router, inter)
        # for other_host in self.host_list:
        #     for inter in other_host.intList:
        #         self.init_update_row(other_host, inter)
        for other_router in self.router_list + self.host_list:
            for inter in router.intList:
                if inter.ip_addr != "0.0.0.0":
                    self.init_update_row(other_router, inter)

    def find_shortest_path(self, dest_ip):
        match_rows = []
        for routing_row in self.table:
            if IPAddress(dest_ip) in self.get_network_id(routing_row):
                if IPAddress(routing_row.dest_ip.strip()) == IPAddress(dest_ip):  # send the data frame if its connected
                    return routing_row
                else:
                    match_rows.append(routing_row)
        longest_match_list = self.find_longest_match_network(dest_ip, match_rows)
        if len(longest_match_list) == 1:
            return longest_match_list[0]
        elif len(longest_match_list) > 1:
            # find the shortest path if there are more than one paths to routing
            hops_list = [routing_row.metric for routing_row in match_rows]
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
            # print "max_value=" + str(max_value)
            max_index_list = [i for i, value in enumerate(common_bit_counts) if value == max_value]
            # print "max_index=" + str(max_index_list)
            return [match_interface_list[index] for index in max_index_list]
        else:
            return []

    def save_table(self, router_table_config):
        if os.path.exists(router_table_config):
            os.remove(router_table_config)
        conf_file = open(router_table_config, 'a+')
        for route_row in self.table:
            line = "%s : %s : %s : %d : %d \n" % (route_row.dest_ip, route_row.next_ip, route_row.inter_ip,
                                                  route_row.net_mask, route_row.metric)
            conf_file.write(line)
        conf_file.close()

    def load_table_config(self, router_table_config):
        if os.path.exists(router_table_config):
            config_file = open(router_table_config, "r")
            for line in config_file.readlines():
                line = line.split(":")
                route_row = RoutingRow(dest_ip=line[0].strip(), next_ip=line[1].strip(),
                                       inter_ip=int(line[3].strip()), net_mask=line[2].strip(),
                                       metric=int(line[4].strip()))
                self.table.append(route_row)


if __name__ == "__main__":
    # rt1 = RoutingRow("10.10.10.9", "10.10.10.11",)
    # rt2 = RoutingRow("10.10.10.11", "10.10.10.10")

    # rb = RoutingTable()
    # rb.table.append(rt1)
    # rb.table.append(rt2)
    # print "longest match:", rb.find_longest_match_network("10.10.10.10")
    if IPNetwork("192.168.1.20/255.255.255.0") == IPNetwork("192.168.1.3/255.255.255.0"):
        print IPNetwork("192.168.1.20/255.255.255.0")
