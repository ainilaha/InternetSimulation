import os
from Tkinter import *
import Tkinter as tK

import struct

from ip import IPDatagram
from logger import LOG
from window import InternetChatDialog
from functools import partial


class ChatWindow(InternetChatDialog):
    def __init__(self, name, master=None, host=None, is_server=False):
        InternetChatDialog.__init__(self, name, master=master, host=host, is_server=is_server)
        self.send_msg["command"] = self.send_message
        self.host_list = []

    def send_message(self):
        message = self.name + ": " + self.inputText.get(1.0, END)
        message = os.linesep + str(message).strip() + os.linesep
        self.historyText.insert(END, message)
        self.inputText.delete(1.0, END)
        if self.current_socket:
            # create data packet and put is host send queue
            self.current_socket.send(data=message)
        else:
            LOG.warning("There is no socket connected!")

    def show_ip(self):
        ip = self.host.intList[0].ip_addr
        message = "local IP: %s \n" % str(ip)
        self.message_queue.put(message)
        LOG.info(message)

    def enter_keys(self, event):
        self.send_message()

    @staticmethod
    def create_chat_window(local_host, host_list, server_indexes):
        root = Tk()
        is_server = False
        if host_list.index(local_host) in server_indexes:
            is_server = True
        else:
            is_server = False
        app = ChatWindow(local_host.name, master=root, host=local_host,is_server=is_server)
        app.host_list = host_list
        app.host = local_host
        app.inputText.bind("<Return>", app.enter_keys)
        menu = Menu(root)
        root.config(menu=menu)
        hosts = Menu(menu)
        if host_list.index(local_host) in server_indexes:
            menu.add_cascade(label="SERVER", menu=hosts)
            hosts.add_command(label="Show IP", command=app.show_ip)
            app.server_accept.start()
        else:
            menu.add_cascade(label="Hosts", menu=hosts)
            hosts.add_command(label="Show IP", command=app.show_ip)
            for host in host_list:
                if host != local_host and host_list.index(host) in server_indexes:
                    action_with_arg = partial(app.set_target_ip, host)
                    hosts.add_command(label="Connect to:" + host.name, command=action_with_arg)

        root.title(app.name)
        # root.mainloop()
        return app

    def winfo_screenmmwidth(self):
        return Misc.winfo_screenmmwidth(self)


class ChatWindowCreator(Frame):
    def __init__(self):
        tK.Frame.__init__(self)
        self.host_list = []
        self.server_indexes = []
        self.pack()
        self.master.title("ChatWindowCreator")
        # self.button1 = tK.Button(self, text="Close", command=self.quit)
        # self.button1.pack()

    def new_window(self):
        for host_simulator in self.host_list:
            win_chat = ChatWindow.create_chat_window(host_simulator, self.host_list,self.server_indexes)
            host_simulator.chat_window = win_chat
            # if self.host_list.index(host_simulator) in self.server_indexes:
            #     win_chat.server_accept.start()


if __name__ == "__main__":
    rc = ChatWindowCreator()
    rc.new_window()
    rc.mainloop()
