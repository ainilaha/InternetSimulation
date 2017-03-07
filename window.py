import multiprocessing
import socket
import threading
from Tkinter import *
from Queue import Empty

from logger import LOG
from server_socket_simulator import ServerSocketSimulator
from socket_simulator import SocketSimulator


class InternetChatDialog(Frame):
    def __init__(self, name, master=None, host=None, is_server=False):
        Frame.__init__(self, master)
        self.name = name
        self.host = host
        self.QUIT = Button(self)
        if not is_server:
            self.QUIT["text"] = "Disconnect"
            self.QUIT["fg"] = "red"
            self.QUIT["command"] = self.quit_connect
            self.QUIT.pack({"side": "left"})
        self.send_msg = Button(self)
        self.send_msg["text"] = "Send",
        # self.send_msg["command"] = self.send_message
        self.send_msg.pack({"side": "left"})
        self.historyText = Text(master, height=18, width=50)
        self.historyText.pack()
        self.inputText = Text(master, height=3, width=50)
        self.inputText.pack()
        self.pack(side=RIGHT)
        self.message_queue = multiprocessing.Queue()
        self.current_socket = None
        self.server_socket = None
        self.client_socket = None
        self.server_accept = threading.Thread(target=self.keep_accept)
        # self.server_accept.start()
        self.master.after(100, self.check_queue_poll, self.message_queue)

    def check_queue_poll(self, c_queue):
        try:
            message = c_queue.get(0)
            self.historyText.insert(END, message)
        except Empty:
            pass
        finally:
            self.master.after(100, self.check_queue_poll, c_queue)

    def keep_accept(self):
        '''
        keep accept can grantee that the host can switch the host from a client to a server
        :return:
        '''
        LOG.info(self.host.name + " has set as a server now..................")
        if not self.server_socket:
            self.server_socket = ServerSocketSimulator(self.host)
        self.server_socket.accept()
        self.current_socket = self.server_socket
        if not self.client_socket:
            self.current_socket = self.server_socket
        else:
            self.client_socket.close()
            self.client_socket = None

    def set_target_ip(self, host):
        LOG.info(self.host.name + ": sending TCP connect to: " + str(host.intList[0].ip_addr))
        if host.chat_window.current_socket:
            message = "Server %s Occupied by %s \n" % (host.name, socket.inet_ntoa(host.chat_window.current_socket.ip_dest))
            self.message_queue.put(message)
            LOG.warning(message)
            return
        if not self.client_socket:
            self.client_socket = SocketSimulator(self.host)
        self.client_socket.connect((host.intList[0].ip_addr, 80))
        self.current_socket = self.client_socket
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None

    def quit_connect(self):
        LOG.info(self.host.name + ":closing the connection...........................")
        if self.client_socket:
            self.client_socket.close()
        LOG.info(self.host.name + ":connection has been closed...........................")
