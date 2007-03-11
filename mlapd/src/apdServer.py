import socket
import asyncore
import asynchat


class APDChannel(asynchat.async_chat):
    def __init__(self, server, conn, addr):
        asynchat.async_chat.__init__(self, conn)
        self.__server = server
        self.__conn = conn
        self.__addr = addr
        self.__map = {}
        self.set_terminator('\r\n')

    # Overrides base class for convenience
    def push(self, msg):
        asynchat.async_chat.push(self, msg + '\r\n')

    # Implementation of base class abstract method
    def collect_incoming_data(self, data):
        if data.find('=') is not -1:
            key = data.split('=')[0]
            value = data.split('=')[1]
            self.__map[key] = value
        elif data is '':
            #handle_map
            pass
        else:
            self.push('action=defer_if_permit Service temporarily unavailable')
            asynchat.async_chat.handle_close(self)

    # Implementation of base class abstract method
    def found_terminator(self):
        print self.__map
        

class APDServer(asyncore.dispatcher):
    def __init__(self, localaddr):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(localaddr)
        self.listen(5)

    def handle_accept(self):
        conn, addr = self.accept()
        channel = APDChannel(self, conn, addr)


if __name__ == '__main__':
    localaddr = ('',7777)
    daemon = APDServer(localaddr)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass
