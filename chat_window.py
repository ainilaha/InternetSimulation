from Tkinter import *
import Tkinter as tK

import struct

from ip import IPDatagram
from router import Router
from window import InternetChatDialog
import multiprocessing
from functools import partial
from time import sleep


class ChatWindow(InternetChatDialog):
    def __init__(self, name, master=None, queue=None):
        InternetChatDialog.__init__(self, name, master=master, queue=queue)
        self.send_msg["command"] = self.send_message
        self.router = None

    def send_message(self):
        message = self.name + ": " + self.inputText.get(1.0, END)
        self.historyText.insert(END, message)
        self.inputText.delete(1.0, END)
        if self.target_index >= 0:
            t1 = multiprocessing.Process(target=put_message_queue,
                                         args=(routerList[self.target_index].chat_window.queue, message,))
            t1.start()
            t1.join()

    def enter_keys(self, event):
        self.send_message()

    @staticmethod
    def create_chat_window(name, current_index, queue):
        root = Tk()
        app = ChatWindow(name, master=root, queue=queue)
        app.inputText.bind("<Return>", app.enter_keys)
        menu = Menu(root)
        root.config(menu=menu)
        routers = Menu(menu)
        menu.add_cascade(label="Routers", menu=routers)
        for i in range(1, 6):
            if i != current_index:
                action_with_arg = partial(app.set_target_index, i - 1)
                routers.add_command(label="Router" + str(i), command=action_with_arg)

        root.title(app.name)
        # root.mainloop()
        return app

    def winfo_screenmmwidth(self):
        return Misc.winfo_screenmmwidth(self)


class RouterCreator(Frame):
    def __init__(self):
        tK.Frame.__init__(self)
        self.no_router = 1
        self.pack()
        self.master.title("RouterCreator")
        self.button1 = tK.Button(self, text="Close", command=self.quit)
        self.button1.pack()

    def new_window(self):
        router_list = []
        while self.no_router <= 5:
            queue = multiprocessing.Queue()
            queue.cancel_join_thread()  # or else thread that puts data will not term
            app = ChatWindow.create_chat_window("Router" + str(self.no_router), self.no_router, queue)
            router = Router("Router" + str(self.no_router))
            router.chat_window = app
            router_list.append(router)
            self.no_router += 1
        return router_list


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
    rc = RouterCreator()
    routerList = rc.new_window()
    rc.mainloop()
