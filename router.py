import os
import random

###########################################################
# This class simulated network interfaces of routers
#
###########################################################


class Interface:
    def __init__(self):
        self.type = "empty type"  # faster 0  ser 1
        self.name = "empty name"  # faster 0/0, faster 1/1, ser 0/0, ser 0/1
        self.mac = ""
        self.IP = "0.0.0.0"

    # this method will convert Mac address to convention format eg
    # eg ec-17-2f-47-82-6c
    @staticmethod
    def insert_dash(string):
        index = 2
        while index < 15:
            string = string[:index] + '-' + string[index:]
            index += 3
        return string

    def set_mac(self, string):
        self.mac = self.insert_dash(string)


class Router:
    def __init__(self, name):
        self.intList = []
        self.name = name
        self.initialize_router()
        self.message_content = ""
        self.chat_window = None

    def initialize_router(self):
        int_name_list = "faster 0/0", "faster 1/1", "ser 0/0", "ser 0/1"
        int_type_list = (1, 1, 0, 0)
        for i in range(0, 4):  # each router equiped with four ports
            mac = random.getrandbits(48)  # random generate 48-bit Mac Address
            mac = str(hex(mac))[3:]  # format mac as hex and discard hex prefix 0x to convenient to observed
            interface = Interface()
            interface.set_mac(mac)
            interface.name = int_name_list[i]
            interface.type = int_type_list[i]
            self.intList.append(interface)

    # def sub_network(self):
    def save_config(self):
        config_file = "config/" + self.name
        if os.path.exists(config_file):
            os.remove(config_file)
        conf_file = open(config_file, 'a+')  # Trying to create a new file or open one
        for port in self.intList:
            conf_file.write(port.name + " : " + str(port.type) + " : "+ port.IP + " : " + port.mac + "\n")
        conf_file.close()

    def show_config(self):
        for port in self.intList:
            print port.name + " : " + str(port.type) + " : " + port.IP + " : " + port.mac + "\n"
            print "----------------------------------------\n"

    def message_port(self, conn):
        conn.send(self.name + ":" + self.message_content)
        message = conn.recv()
        print message + "\n"
        conn.close()
        return message


if __name__ == "__main__":
    router = Router("Router")
