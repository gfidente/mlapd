#!/bin/env python

import optparse
import socket
import asyncore
import asynchat
import datactrl.ldapmdl


VERSION="0.1"

DEFER_ACTION="DEFER_IF_PERMIT Service temporarily unavailable"

class apdChannel(asynchat.async_chat):
    """manage apd channel and launches database query tasks
    
    Parameters:
        conn comes back from an accepted asyncore.dispatcher
    """
    
    def __init__(self, conn):
        asynchat.async_chat.__init__(self, conn)
        self.map = {}
        self.action = "action="
        self.set_terminator('\n')

    # Overrides base class for convenience
    def push(self, msg):
        asynchat.async_chat.push(self, msg + '\n')

    # Implementation of base class abstract method
    def collect_incoming_data(self, data):
        if data.find('=') != -1:
            key = data.split('=')[0]
            value = data.split('=')[1]
            value = value.strip('\r')
            self.map[key] = value
        elif data == '\r':
            modeler = datactrl.ldapmdl.Modeler()
            self.action = self.action + modeler.handle_data(self.map)
            self.push(self.action)
            asynchat.async_chat.handle_close(self)
        else:
            self.action = self.action + DEFER_ACTION
            self.push(self.action)
            asynchat.async_chat.handle_close(self)

    # Implementation of base class abstract method
    def found_terminator(self):
        pass


class apdSocket(asyncore.dispatcher):
    """bind to localaddr, accept connections and launches apd channels
    
    Parameters:
        localaddr is in the form (interface, port)
    """
    
    def __init__(self, localaddr):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(localaddr)
        self.listen(5)

    def handle_accept(self):
        conn, addr = self.accept()
        channel = apdChannel(conn)


if __name__ == '__main__':
    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(usage=usage, version="%prog " + VERSION)
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
