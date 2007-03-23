import optparse
import logging
import socket
import asyncore
import asynchat
import ldapmodel


__version__ = "0.2"

class apdChannel(asynchat.async_chat):    
    ACTION_PREFIX = "action="
    ACCEPT_ACTION = "OK"
    DEFER_ACTION = "DEFER_IF_PERMIT Service temporarily unavailable"
    
    def __init__(self, conn, remoteaddr):
        asynchat.async_chat.__init__(self, conn)
        self.buffer = []
        self.map = {}
        self.set_terminator('\n')
        logging.info("connection from " + remoteaddr[0])

    def push(self, msg):
        asynchat.async_chat.push(self, msg + '\n')

    def collect_incoming_data(self, data):
        self.buffer.append(data)

    def found_terminator(self):
        if len(self.buffer) is not 0:
            line = self.buffer.pop()
            logging.debug("got: " + line)
            if line.find('=') != -1:
                key = line.split('=')[0]
                value = line.split('=')[1]
                self.map[key] = value
        elif len(self.map) is not 0:
            try:
                modeler = ldapmodel.Modeler()
                result = modeler.handle_data(self.map)
                if result != None:
                    action = self.ACTION_PREFIX + result
                else:
                    action = self.ACTION_PREFIX + self.ACCEPT_ACTION
                    logging.warning("no useful action found!")
            except:
                action = self.ACTION_PREFIX + self.DEFER_ACTION
                logging.error("unexpected modeler error, ldap misconfiguration?")
                #import sys
                #logging.debug(sys.exc_info())
            logging.debug("replying: " + action)
            self.push(action)
            self.push('')
            asynchat.async_chat.handle_close(self)
            logging.info("closing connection")
        else:
            action = self.ACTION_PREFIX + self.DEFER_ACTION
            logging.debug("replying: " + action)
            self.push(action)
            self.push('')
            asynchat.async_chat.handle_close(self)
            logging.info("closing connection")


class apdSocket(asyncore.dispatcher):    
    def __init__(self, localaddr):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(localaddr)
        self.listen(5)
        ip, port = localaddr
        logging.info("listening on " + ip + ":" + str(port))


    def handle_accept(self):
        conn, remoteaddr = self.accept()
        channel = apdChannel(conn, remoteaddr)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(thread)s %(levelname)s %(message)s', datefmt='%d-%m-%Y, %H:%M:%S')
    logging.info("starting version " + __version__)
    
    usage = "usage: %prog [options]"
    
    parser = optparse.OptionParser(usage=usage, version="%prog " + __version__)
    parser.add_option("-p", action="store", type="int", dest="port", help="port where the daemon will listen")
    parser.add_option("-i", action="store", type="string", dest="iface", help="interface where the daemon will listen")
    parser.set_defaults(iface="127.0.0.1")
    parser.set_defaults(port=7777)
    
    options, args = parser.parse_args()
    
    localaddr = (options.iface, options.port)
    daemon = apdSocket(localaddr)
    
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass