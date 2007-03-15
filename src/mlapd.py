import optparse
import logging
import socket
import asyncore
import asynchat
import ldapmodel


VERSION="0.1"

class apdChannel(asynchat.async_chat):    
    ACTION_PREFIX = "action="
    DEFER_ACTION = "DEFER_IF_PERMIT Service temporarily unavailable"
    
    def __init__(self, conn, addr):
        asynchat.async_chat.__init__(self, conn)
        self.buffer = None
        self.map = {}
        self.set_terminator('\n')
        logging.info("connection accepted from " + self.addr[0])

    def push(self, msg):
        asynchat.async_chat.push(self, msg + '\n')

    def collect_incoming_data(self, data):        
        self.buffer = data

    def found_terminator(self):
        if self.buffer != None and self.buffer.find('=') != -1:
            key = self.buffer.split('=')[0]
            value = self.buffer.split('=')[1]
            self.map[key] = value
            self.buffer = None
        elif self.buffer == None and self.map != {}:
            modeler = ldapmodel.Modeler()
            action = self.ACTION_PREFIX + modeler.handle_data(self.map)
            self.push(action)
            self.push('')
            asynchat.async_chat.handle_close(self)
        else:
            action = self.ACTION_PREFIX + self.DEFER_ACTION
            self.push(action)
            asynchat.async_chat.handle_close(self)


class apdSocket(asyncore.dispatcher):    
    def __init__(self, localaddr):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(localaddr)
        self.listen(5)


    def handle_accept(self):
        conn, addr = self.accept()
        channel = apdChannel(conn, addr)


if __name__ == '__main__':
    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(usage=usage, version="%prog " + VERSION)
    parser.add_option("-p", action="store", type="int", dest="port", help="port where the daemon will listen")
    parser.add_option("-i", action="store", type="string", dest="iface", help="interface where the daemon will listen")
    parser.set_defaults(iface="127.0.0.1")
    parser.set_defaults(port=7777)
    options, args = parser.parse_args()
    
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(thread)s %(levelname)s %(message)s', datefmt='%d-%m-%Y, %H:%M:%S')
    
    localaddr = (options.iface, options.port)
    daemon = apdSocket(localaddr)
    
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass