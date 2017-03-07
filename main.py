import menu
import struct

from chat_window import ChatWindowCreator
from host_simulator import HostSimulator
from ip import IPDatagram
from logger import LOG
from router_simulator import RouterSimulator


class ConfigMenu:
    def __init__(self):
        self.router_list = []
        self.host_list = []
        self.chat_win = ChatWindowCreator()

    def create_routers_and_host(self, router_number=5):
        i = 1
        while i < router_number+1:
            router_simulator = RouterSimulator("Router" + str(i))
            host_simulator = HostSimulator("Host" + str(i))
            self.router_list.append(router_simulator)
            self.host_list.append(host_simulator)
            i += 1
        for router_simulator in self.router_list:
            router_simulator.route_table.router_list = self.router_list
            router_simulator.route_table.host_list = self.host_list
            router_simulator.route_table.init_routing_table(router_simulator)
            router_simulator.arp_mac_table.router_list = self.router_list
            router_simulator.arp_mac_table.host_list = self.host_list

        for host_simulator in self.host_list:
            host_simulator.route_table.router_list = self.router_list
            host_simulator.route_table.host_list = self.host_list
            host_simulator.arp_mac_table.router_list = self.router_list
            host_simulator.arp_mac_table.host_list = self.host_list
            host_simulator.route_table.init_routing_table(host_simulator)

    def create_and_set_number_device(self):
        value = raw_input("Please input routers numbers(Integer):")
        value = int(value)
        self.create_routers_and_host(value)
        LOG.info("Notice: %d hosts and %d routers have been created" % (value, value))


    @staticmethod
    def show_config(menu):
        print "Router config menu \n"

    def config_router_ip(self):
        if not len(self.host_list):
            LOG.warning("Please create routers and host first!!")
            return
        value = raw_input("Input Router Number(1 to %d):" % len(self.router_list))
        print "Router Number is:" + value
        router = self.router_list[int(value) - 1]
        i = 0
        while i < 4:
            ip = raw_input("Input IP address of int "+str(i+1)+":")
            ip = str(ip).strip()
            if ip != "" and IPDatagram.is_valid_ipv4(ip):
                router.intList[i].ip_addr = ip
            else:
                LOG.info("%s is empty or an illegal ip address!" % ip)
            i += 1
        router.route_table.init_routing_table(router)
        router.show_config()
        router.save_config()
        router.arp_mac_table.show_table()

    def config_host_ip(self):
        if not len(self.host_list):
            LOG.warning("Please create routers and host first!!")
            return
        value = raw_input("Input host Number(1 to %d):" % len(self.host_list))
        print "Host Number is:" + value
        host_simulator = self.host_list[int(value) - 1]
        ip = raw_input("Input IP address of host:")
        ip = str(ip).strip()
        if ip != "" and IPDatagram.is_valid_ipv4(ip):
            host_simulator.intList[0].ip_addr = str(ip)
            host_simulator.show_config()
            host_simulator.save_config()
            host_simulator.arp_mac_table.show_table()
        else:
            LOG.info("%s is an empty or illegal ip address!" % ip)

    def show_table(self):
        # self.router_list[0].route_table.show_table()
        for router in self.router_list:
            LOG.info(router.name + ":****************************:")
            router.route_table.show_table()
        for host in self.host_list:
            LOG.info(host.name + ":*****************************:")
            host.route_table.show_table()

    def select_servers(self):
        if not len(self.host_list):
            LOG.warning("Please create routers and host first!!")
            return
        values = raw_input("select hosts as server Number(1 to %d), split as \',\' if more than one:" %
                          len(self.host_list))
        values = str(values).strip().split(",")
        for value in values:
            self.chat_win.server_indexes.append(int(value)-1)

    def start_chat_window(self):
        print "--------------start_chat_window-----------"
        self.chat_win.host_list = self.host_list
        self.chat_win.new_window()
        self.chat_win.mainloop()
        for win_host in self.host_list:
            win_host.chat_window.server_accept.join()
            win_host.chat_window.current_socket.receiving_tcp.join()

if __name__ == "__main__":
    conf = ConfigMenu()
    mainMenu = menu.Menu("Routers config", conf.show_config)
    mainMenu.explicit()
    options = [{"name": "Create Router", "function": conf.create_and_set_number_device},
               {"name": "Config Host IP", "function": conf.config_host_ip},
               {"name": "config Router IP", "function": conf.config_router_ip},
               {"name": "Show Routing Table", "function": conf.show_table},
               {"name": "Select Servers", "function": conf.select_servers},
               {"name": "Open Chat Window", "function": conf.start_chat_window}]

    mainMenu.addOptions(options)
    mainMenu.open()
    for router in conf.router_list:
        router.receive.join()
        router.routing_packets.join()
        router.interface.send_thread.join()
        router.interface.receiving.join()
    for host in conf.host_list:
        host.host_receiving.join()