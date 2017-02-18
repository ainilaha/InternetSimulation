import menu
import struct

from arp_mac_table import ARPnMACTable, ARPnMACRow
from ethernet import EthernetFrame
from ip import IPDatagram
from router_simulator import RouterSimulator
from routing_table import RoutingRow


class ConfigMenu:
    def __init__(self):
        self.router_list = []
        self.create_routers()

    def create_routers(self):
        i = 1
        while i < 6:
            router_simulator = RouterSimulator("Router" + str(i))
            i += 1
            router_simulator.show_config()
            self.router_list.append(router_simulator)

    @staticmethod
    def show_config(menu):
        print "Router config menu \n"

    def config_ip(self):
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
        router.load_config()
        router.arp_mac_table.show_table()

    def create_test_frame(self):
        src_ip = struct.pack('4B', 100, 168, 10, 10)
        des_ip = struct.pack('4B', 192, 168, 1, 10)
        ip_data = IPDatagram(src_ip, des_ip, data="hello world")

        src_mac = ARPnMACTable.get_mac_pack(self.router_list[0].intList[0].mac)
        des_mac = ARPnMACTable.get_mac_pack(self.router_list[1].intList[0].mac)
        e = EthernetFrame(src_mac, des_mac, tcode=0x0800, data=ip_data.pack())
        return e.pack()


    def show_table(self):
        # self.router_list[0].route_table.show_table()
        self.router_list[0].arp_mac_table.show_table()

    def test_send(self):
        eth = self.create_test_frame()
        routing_row = RoutingRow(dest_ip="192.168.1.10", inter_ip="192.168.1.1")
        self.router_list[0].route_table.table.append(routing_row)
       # mac_row = ARPnMACRow(ip_addr="192.168.1.10", mac=self.router_list[1].intList[0].mac, mac_type=0)
       # mac_row.interface = self.router_list[1].intList[0]
       # self.router_list[0].arp_mac_table.mac_table.append(mac_row)
        self.router_list[0].received_frame_data_queue.put(eth)
        self.router_list[0].arp_mac_table.router_list.append(self.router_list[0])
        self.router_list[0].arp_mac_table.router_list.append(self.router_list[1])
        self.router_list[1].arp_mac_table.router_list.append(self.router_list[0])
        self.router_list[1].arp_mac_table.router_list.append(self.router_list[1])
        print "len router = " + str(len(self.router_list[0].arp_mac_table.router_list))


if __name__ == "__main__":
    conf = ConfigMenu()
    mainMenu = menu.Menu("Routers config", conf.show_config)
    mainMenu.explicit()
    options = [{"name": "config ip", "function": conf.config_ip},
               {"name": "show routing table", "function": conf.show_table},
               {"name": "test_send", "function": conf.test_send}]

    mainMenu.addOptions(options)
    mainMenu.open()
    for router in conf.router_list:
        router.receive.join()
        router.routing_packets.join()
        router.interface.send_thread.join()
