#!/usr/bin/python

ACCEPT_ACTION = "OK"
DEFER_ACTION = "DEFER_IF_PERMIT Service temporarily unavailable"
REJECT_ACTION = "REJECT Not Authorized"

# ldapmodel

import ConfigParser
import ldap

class LdapModel:
    def __init__(self):
        self.config = ConfigParser.SafeConfigParser()
        self.config.readfp(open(options.configfile))
    
        __URL = self.config.get("LDAP_SERVER", "URL")
        __BINDDN = self.config.get("LDAP_SERVER", "BINDDN")
        __BINDPWD = self.config.get("LDAP_SERVER", "BINDPWD")        

        self.server = ldap.initialize(__URL)       
        if __BINDDN != "":
            self.server.simple_bind(__BINDDN, __BINDPWD)
    
    
    def __get_list_policy(self, listname):        
        self.config.set("LDAP_DATA", "recipient", listname)

        baseDN = self.config.get("LDAP_SERVER", "ROOTDN")
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = [self.config.get("LDAP_DATA", "POLICYATTR")]
        searchFilter = self.config.get("LDAP_DATA", "LISTFILTER")
    
        results_id = self.server.search(baseDN, searchScope, searchFilter, retrieveAttributes)
        while True:
            result_type, result_data = self.server.result(results_id, 0)
            if (result_data == []):
                return None, None
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_dn, result_set = result_data[0]
                    for attribute in retrieveAttributes:
                        return result_dn, result_set[attribute][0]
                        
    
    def __get_list_authorized(self, listdn, listname, internals):
        self.config.set("LDAP_DATA", "recipient", listname)
        
        baseDN = listdn
        searchScope = ldap.SCOPE_BASE
        if internals:
            retrieveAttributes = [self.config.get("LDAP_DATA", "SUBSCRATTRIBUTE")]
        else:
            retrieveAttributes = [self.config.get("LDAP_DATA", "ALLWDATTRIBUTE")]
        searchFilter = self.config.get("LDAP_DATA", "LISTFILTER")
    
        results_id = self.server.search(baseDN, searchScope, searchFilter, retrieveAttributes)
        while True:
            result_type, result_data = self.server.result(results_id, 0)
            if (result_data == []):
                return None
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_dn, result_set = result_data[0]
                    for attribute in retrieveAttributes:
                        return result_set[attribute]

    
    def __get_action(self, listname, sender):        
        listdn, listpolicy = self.__get_list_policy(listname)
        
        if listdn == None or listpolicy == None:
            return None
        else:
            if listpolicy == "open":
                return ACCEPT_ACTION
            elif listpolicy == "domain":
                senderdomain = sender.split("@")[1]
                listdomain = listname.split("@")[1]
                if listdomain == senderdomain:
                    return ACCEPT_ACTION
                else:
                    return REJECT_ACTION
            elif listpolicy == "filter":
                authorized_submitters = self.__get_list_authorized(listdn, listname, False)
                if authorized_submitters != None:
                    addresses = set(authorized_submitters)
                    for address in addresses:
                        if address.lower() == sender.lower():
                            return ACCEPT_ACTION
                    return REJECT_ACTION
            elif listpolicy == "internals":
                authorized_submitters = self.__get_list_authorized(listdn, listname, True)
                if authorized_submitters != None:
                    addresses = set(authorized_submitters)
                    for address in addresses:
                        if address.lower() == sender.lower():
                            return ACCEPT_ACTION
                    return REJECT_ACTION
                else:
                    return DEFER_ACTION
    
    
    def handle_data(self, map):
        if map.has_key("sender") and map.has_key("recipient"):
            sender = map["sender"]
            recipient = map["recipient"]
            action = self.__get_action(recipient, sender)
            return action
        else:
            return DEFER_ACTION

# mlapd.py

__version__ = "0.3"

import socket
import asyncore
import asynchat

class apdChannel(asynchat.async_chat):    
    def __init__(self, conn, remoteaddr):
        asynchat.async_chat.__init__(self, conn)
        self.key = ''
        self.value = ''
        self.line = ''
        self.buffer = []
        self.map = {}
        self.set_terminator('\n')
        logging.info("got connection from " + remoteaddr[0])

    def push(self, msg):
        asynchat.async_chat.push(self, msg + '\n')

    def collect_incoming_data(self, data):
        self.buffer.append(data)

    def found_terminator(self):
        if len(self.buffer) is not 0:
            self.line = self.buffer.pop()
            logging.debug("parsing: " + self.line)
            if self.line.find('=') != -1:
                self.key = self.line.split('=')[0]
                self.value = self.line.split('=')[1]
                self.map[self.key] = self.value
        elif len(self.map) is not 0:
            try:
                self.modeler = LdapModel()
                self.result = self.modeler.handle_data(self.map)
                if self.result != None:
                    self.action = "action=" + self.result
                else:
                    self.action = "action=" + ACCEPT_ACTION
                    logging.warning("no useful action found, maybe the recipient is not a mailing list or doesn't have valid policy attribute")
            except:
                self.action = "action=" + DEFER_ACTION
                logging.error("modeler error, probably due to misconfiguration or data population error")
                logging.error("please submit a bug at http://code.google.com/p/mlapd/issues if you think it should work")
                raise
            logging.debug("replying: " + self.action)
            self.push(self.action)
            self.push('')
            asynchat.async_chat.handle_close(self)
            logging.info("closing connection")
        else:
            self.action = "action=" + DEFER_ACTION
            logging.warning("no input data received")
            logging.debug("replying: " + self.action)
            self.push(self.action)
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
        self.ip, self.port = localaddr
        logging.info("started and listening on " + self.ip + ":" + str(self.port))

    def handle_accept(self):
        self.conn, self.remoteaddr = self.accept()
        apdChannel(self.conn, self.remoteaddr)


# daemonize

import os
import time

class NullDevice:
    def write(self, s):
        pass

def daemonize():
    if (not os.fork()):
        # get our own session
        os.setsid()
        if (not os.fork()):
            # hang around till adopted by init
            ppid = os.getppid()
            while (ppid != 1):
                time.sleep(0.5)
                ppid = os.getppid()
        else:
            # time for child to die
            os._exit(0)
    else:
        # wait for child to die and then bail
        os.wait()
        os._exit(0)
        

# initialization

import optparse
import logging
import os
import sys

if __name__ == '__main__':
    mydir = os.path.dirname(__file__)
    os.chdir(mydir + "/../")

    usage = "usage: mlapd [options]"
    cmdline = optparse.OptionParser(usage=usage, version="mlapd " + __version__)
    cmdline.add_option("-d", action="store_true", dest="debug", help="enables debug output in the logfile")
    cmdline.add_option("-p", action="store", type="int", dest="port", help="port where the daemon will listen [default: %default]")
    cmdline.add_option("-i", action="store", type="string", dest="iface", help="interface where the daemon will listen [default: %default]")
    cmdline.add_option("-l", action="store", type="string", dest="logfile", help="path to the logfile [default: %default]")
    cmdline.add_option("-c", action="store", type="string", dest="configfile", help="path to the configfile [default: %default]")
    cmdline.add_option("-P", action="store", type="string", dest="pidfile", help="path to the pidfile [default: %default]")
    cmdline.set_defaults(debug=False)
    cmdline.set_defaults(iface="127.0.0.1")
    cmdline.set_defaults(port=7777)
    cmdline.set_defaults(logfile="var/log/mlapd.log")
    cmdline.set_defaults(configfile="etc/ldapmodel.conf")
    cmdline.set_defaults(pidfile="var/run/mlapd.pid")
    options, args = cmdline.parse_args()
    localaddr = (options.iface, options.port)
    if options.debug is False:
        loglevel = logging.INFO
    else:
        loglevel = logging.DEBUG
    
    try:
        logging.basicConfig(filename=options.logfile, level=loglevel, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    except:
        logging.basicConfig(level=loglevel, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        logging.error("error while opening the logfile at " + options.logfile + ", continuing on stdout")

    apdSocket(localaddr)
    daemonize()
    
    try:
        f = open(options.pidfile, 'w')
        f.write(str(os.getpid()))
        f.close()
    except:
        logging.error("error while opening the pidfile at " + options.pidfile + ", ensure directory is writable, exiting")
        os._exit(1)

    sys.stdin.close()
    sys.stdout = NullDevice()
    sys.stderr = NullDevice()

    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass
