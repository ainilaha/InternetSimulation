import menu
import struct

from arp_mac_table import ARPnMACTable
from ethernet import EthernetFrame
from host_simulator import HostSimulator
from ip import IPDatagram
from router_simulator import RouterSimulator
from routing_table import RoutingRow


class ConfigMenu:
    def __init__(self):
        self.router_list = []
        self.host_list = []
        self.create_routers()

    def create_routers(self):
        i = 1
        while i < 4:
            router_simulator = RouterSimulator("Router" + str(i))
            host_simulator = HostSimulator("Host" + str(i))
            self.router_list.append(router_simulator)
            self.host_list.append(host_simulator)
            i += 1

    @staticmethod
    def show_config(menu):
        print "Router config menu \n"

    def config_router_ip(self):
        value = raw_input("Input Router Number(1 to 5):")
        print "Router Number is:" + value
        router = self.router_list[int(value) - 1]
        i = 0
        while i < 4:
            ip = raw_input("Input IP address of int "+str(i+1)+":")
            router.intList[i].ip_addr = str(ip)
            i += 1
        router.show_config()
        router.save_config()
        router.arp_mac_table.show_table()

    def config_host_ip(self):
        value = raw_input("Input host Number(1 to 5):")
        print "Host Number is:" + value
        host_simulator = self.host_list[int(value) - 1]
        ip = raw_input("Input IP address of host:")
        host_simulator.interface.ip_addr = str(ip)
        host_simulator.show_config()
        host_simulator.save_config()
        host_simulator.load_config()
        host_simulator.arp_mac_table.show_table()

    def create_test_frame(self):
        src_ip = struct.pack('4B', 100, 168, 10, 10)
        des_ip = struct.pack('4B', 192, 168, 1, 10)
        ip_data = IPDatagram(src_ip, des_ip, data="hello world")

        return ip_data.pack()


    def show_table(self):
        # self.router_list[0].route_table.show_table()
        print "---------------------router0----------------------------"
        self.router_list[0].arp_mac_table.show_table()
        self.router_list[0].route_table.show_table()
        print "---------------------router1----------------------------"
        self.router_list[1].arp_mac_table.show_table()
        self.router_list[1].route_table.show_table()
        print "------------------------host 1------------------------"
        self.host_list[1].arp_mac_table.show_table()
        self.host_list[1].route_table.show_table()

    def test_send(self):
        eth = self.create_test_frame()
        routing_row1 = RoutingRow(dest_ip="192.168.1.1", next_ip="10.10.10.2", inter_ip="10.10.10.1")
        self.host_list[0].route_table.table.append(routing_row1)
        routing_row2 = RoutingRow(dest_ip="192.168.1.3", next_ip="12.12.12.12", inter_ip="12.12.12.1")
        self.router_list[0].route_table.table.append(routing_row2)

        routing_row3 = RoutingRow(dest_ip="192.168.1.5", next_ip="192.168.1.8", inter_ip="192.168.1.1")
        self.router_list[1].route_table.table.append(routing_row3)
        routing_row4 = RoutingRow(dest_ip="192.168.1.10", next_ip="192.168.1.5", inter_ip="192.168.1.8")
        self.host_list[1].route_table.table.append(routing_row4)
        self.host_list[0].send_datagram(eth)
        self.router_list[0].arp_mac_table.router_list = self.router_list
        self.router_list[1].arp_mac_table.router_list = self.router_list
        self.router_list[0].arp_mac_table.host_list = self.host_list
        self.router_list[1].arp_mac_table.host_list = self.host_list
        self.host_list[0].arp_mac_table.host_list = self.host_list
        self.host_list[0].arp_mac_table.router_list = self.router_list
        self.host_list[1].arp_mac_table.host_list = self.host_list
        self.host_list[1].arp_mac_table.router_list = self.router_list
        print "len router = " + str(len(self.router_list[0].arp_mac_table.router_list))


if __name__ == "__main__":
    conf = ConfigMenu()
    mainMenu = menu.Menu("Routers config", conf.show_config)
    mainMenu.explicit()
    options = [{"name": "config host ip", "function": conf.config_host_ip},
               {"name": "config router ip", "function": conf.config_router_ip},
               {"name": "show routing table", "function": conf.show_table},
               {"name": "test_send", "function": conf.test_send}]

    mainMenu.addOptions(options)
    mainMenu.open()
    for router in conf.router_list:
        router.receive.join()
        router.routing_packets.join()
        router.interface.send_thread.join()
        router.interface.receiving.join()
    for host in conf.host_list:
        host.host_receiving.join()