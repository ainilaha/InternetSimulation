import socket
from Tkinter import *
import Tkinter as tK

import struct

from ip import IPDatagram
from window import InternetChatDialog
import multiprocessing
from functools import partial


class ChatWindow(InternetChatDialog):
    def __init__(self, name, master=None, queue=None):
        InternetChatDialog.__init__(self, name, master=master, queue=queue)
        self.send_msg["command"] = self.send_message
        self.host_list = []
        self.host = None

    def send_message(self):
        message = self.name + ": " + self.inputText.get(1.0, END)
        self.historyText.insert(END, message)
        self.inputText.delete(1.0, END)
        if self.target_ip != "0.0.0.0":
            # create data packet and put is host send queue
            print "local ip=" + self.host.intList[0].ip_addr
            print "dec ip=" + self.target_ip
            message = str(message).strip()
            ip_data = IPDatagram(ip_src_addr=socket.inet_aton(self.host.intList[0].ip_addr),
                                 ip_dest_addr=socket.inet_aton(self.target_ip),
                                 data=message)

            self.host.send_datagram(ip_data.pack())

    def enter_keys(self, event):
        self.send_message()

    @staticmethod
    def create_chat_window(local_host, host_list, queue):
        root = Tk()
        app = ChatWindow(local_host.name, master=root, queue=queue)
        app.host_list = host_list
        app.host = local_host
        app.inputText.bind("<Return>", app.enter_keys)
        menu = Menu(root)
        root.config(menu=menu)
        hosts = Menu(menu)
        menu.add_cascade(label="Hosts", menu=hosts)
        for host in host_list:
            if host != local_host:
                action_with_arg = partial(app.set_target_ip, host.intList[0].ip_addr)
                hosts.add_command(label=host.name, command=action_with_arg)

        root.title(app.name)
        # root.mainloop()
        return app

    def winfo_screenmmwidth(self):
        return Misc.winfo_screenmmwidth(self)


class ChatWindowCreator(Frame):
    def __init__(self):
        tK.Frame.__init__(self)
        self.host_list = []
        self.pack()
        self.master.title("ChatWindowCreator")
        self.button1 = tK.Button(self, text="Close", command=self.quit)
        self.button1.pack()

    def new_window(self):
        print "--------------------------new_window-----------------------"
        for host_simulator in self.host_list:
            print "--------------------------new_window-------host_simulator----------------" + host_simulator.name
            queue = multiprocessing.Queue()
            queue.cancel_join_thread()  # or else thread that puts data will not term
            win_chat = ChatWindow.create_chat_window(host_simulator, self.host_list, queue)
            host_simulator.chat_window = win_chat


def put_message_queue(queue, message):
    ip = struct.pack('4B', 101, 104, 10, 10)
    print "-------------------ip_data---b-----------------"
    ip_data = IPDatagram(ip, ip, data=str(message))
    print "-------------------ip_data---a-----------------"
    print ip_data.__repr__()
    message = ip_data.pack()
    print message
    queue.put(message)
    # sleep(0.001)  # Besides, the time needed to route packets from one node to another should not be zero.


if __name__ == "__main__":
    rc = ChatWindowCreator()
    rc.new_window()
    rc.mainloop()
