import menu

from router import Router


class ConfigMenu:
    def __init__(self):
        self.routerConfigList = []
        self.create_routers()

    def create_routers(self):
        i = 1
        while i < 6:
            router = Router("Router" + str(i))
            i += 1
            router.show_config()
            self.routerConfigList.append(router)

    @staticmethod
    def show_config(menu):
        print "Router config menu \n"

    def config_ip(self):
        value = raw_input("Input Router Number(1 to 5):")
        print "Router Number is:" + value
        router = self.routerConfigList[int(value) - 1]
        i = 0
        while i < 4:
            ip = raw_input("Input IP address of int "+str(i+1)+":")
            router.intList[i].IP = str(ip)
            i += 1
        router.show_config()
        router.save_config()


    def secondFunc(self):
        print "secondFunc"

    def thirdFunc(self):
        print "thirdFunc"


if __name__ == "__main__":
    conf = ConfigMenu()
    mainMenu = menu.Menu("Routers config", conf.show_config)
    mainMenu.explicit()
    options = [{"name": "config ip", "function": conf.config_ip},
               {"name": "secondOption", "function": conf.secondFunc},
               {"name": "thirdOption", "function": conf.thirdFunc}]

    mainMenu.addOptions(options)
    mainMenu.open()
