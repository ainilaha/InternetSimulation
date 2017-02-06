################################################
# simulated the transfer media
################################################
from multiprocessing import Process, Pipe

from router import Router


class Wire:
    def __init__(self):
        self.name = ""
        self.routerList = []
        self.windowList = []

    @staticmethod
    def create_wire(source_window, target_window):
        source_router_conn, target_router_conn = Pipe()
        source = Process(target=source_window.message_port, args=(source_router_conn,))
        destination = Process(target=target_window.message_port, args=(target_router_conn,))
        destination.start()
        source.start()
        source.join()
        destination.join()


if __name__ == "__main__":
    wire = Wire()
    sourceRouter = Router("R1")
    destinationRouter = Router("R2")
    wire.create_wire(sourceRouter, destinationRouter)
