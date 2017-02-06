from Tkinter import *
from Queue import Empty


class InternetChatDialog(Frame):
    def __init__(self, name, master=None, queue=None):
        Frame.__init__(self, master)
        self.name = name
        self.QUIT = Button(self)
        self.QUIT["text"] = "QUIT"
        self.QUIT["fg"] = "red"
        self.QUIT["command"] = self.quit
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
        self.queue = queue
        self.target_index = -1
        self.master.after(100, self.check_queue_poll, self.queue)

    def check_queue_poll(self, c_queue):
        try:
            message = c_queue.get(0)
            self.historyText.insert(END, message)
        except Empty:
            pass
        finally:
            self.master.after(100, self.check_queue_poll, c_queue)

    def set_target_index(self, i):
        print "Try to connect Router" + str(i)
        self.target_index = i
