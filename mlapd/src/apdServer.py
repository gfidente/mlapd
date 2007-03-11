import socket
import asyncore
import apdChannel


class apdSocket(asyncore.dispatcher):
    "bind to localaddr, accept connections and launches apd channels"
    
    def __init__(self, localaddr):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(localaddr)
        self.listen(5)

    def handle_accept(self):
        conn, addr = self.accept()
        channel = apdChannel.chatChannel(conn, addr)


if __name__ == '__main__':
    localaddr = ('',7777)
    daemon = apdSocket(localaddr)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass
