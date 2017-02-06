from Tkinter import *


class Application(Frame):

    def sendMessage(self):
        print "hi there, everyone!"

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.QUIT = Button(self)
        self.QUIT["text"] = "QUIT"
        self.QUIT["fg"] = "red"
        self.QUIT["command"] = self.quit
        self.QUIT.pack({"side": "left"})
        self.send_msg = Button(self)
        self.send_msg["text"] = "Send",
        self.send_msg["command"] = self.sendMessage
        self.send_msg.pack({"side": "left"})


root = Tk()
text = Text(height=30,width=80)
app = Application(master=root)
root.mainloop()
root.destroy()
