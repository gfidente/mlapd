import ConfigParser
import ldap


ACCEPT_ACTION="OK"
REJECT_ACTION="REJECT Not Authorized"

__config = ConfigParser.SafeConfigParser()
__config.read(["/mnt/hdb8/workspace/mlapd/datactrl/ldapmdl.conf"])


def handle_data(map):
    sender = map["sender"]
    senderdomain = sender.split("@")[1]
    recipient = map["recipient"]
    
    __HOST = __config.get("LDAP_SERVER", "HOST")
    __PORT = __config.getint("LDAP_SERVER", "PORT")
    __ROOTDN = __config.get("LDAP_SERVER", "ROOTDN")
    __BINDDN = __config.get("LDAP_SERVER", "BINDDN")
    __BINDPWD = __config.get("LDAP_SERVER", "BINDPWD")
    
    lserver = ldap.open(__HOST, __PORT)
    lserver.simple_bind_s(__BINDDN, __BINDPWD)
    
    return REJECT_ACTION