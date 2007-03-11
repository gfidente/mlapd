import asynchat


class chatChannel(asynchat.async_chat):
    "manage apd channel and launches database query tasks"
    
    def __init__(self, conn, addr):
        asynchat.async_chat.__init__(self, conn)
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
