import sys
import ConfigParser
import ldap


ACCEPT_ACTION="OK"
DEFER_ACTION="DEFER_IF_PERMIT Service temporarily unavailable"
REJECT_ACTION="REJECT Not Authorized"


__config = ConfigParser.SafeConfigParser()
__config.read([sys.path[0] + "/datactrl/ldapmdl.conf"])


def __get_ldap_connection():
    "Return a connected LDAPObject"
    
    __URL = __config.get("LDAP_SERVER", "URL")
    __BINDDN = __config.get("LDAP_SERVER", "BINDDN")
    __BINDPWD = __config.get("LDAP_SERVER", "BINDPWD")
    
    lserver = ldap.initialize(__URL)
    lserver.simple_bind(__BINDDN, __BINDPWD)
    
    return lserver


def __get_list_policy(server, listname):
    """Return the policy used on a list
    
    Parameters:
        server is an LDAPObject connected
        listname is the mailing list rfc822 address
    """
    
    __config.set("LDAP_DATA", "recipient", listname)
    
    baseDN = __config.get("LDAP_SERVER", "ROOTDN")
    searchScope = ldap.SCOPE_SUBTREE
    retrieveAttributes = [__config.get("LDAP_DATA", "POLICYATTR")]
    searchFilter = __config.get("LDAP_DATA", "LISTFILTER")

    # server.set_option(ldap.sizelimit, 1)
    results_id = server.search(baseDN, searchScope, searchFilter, retrieveAttributes)
    while True:
        result_type, result_data = server.result(results_id, 0)
        if (result_data == []):
            break
        else:
            if result_type == ldap.RES_SEARCH_ENTRY:
                result_dn, result_set = result_data[0]
                for attribute in retrieveAttributes:
                    return result_set[attribute][0]
                    

def __get_action(server, listname, policy, sender):
    """Return the action for Postfix!
    
    Parameters:
        server is an LDAPObject connected
        listname is the mailing list rfc822 address
        policy is the policy used for the list
        sender is the submitter rfc822 address
    """
    
    return REJECT_ACTION


def handle_data(map):
    sender = map["sender"]
    senderdomain = sender.split("@")[1]
    recipient = map["recipient"]
    
    server = __get_ldap_connection()
    
    listpolicy = __get_list_policy(server, recipient)
    
    return __get_action(server, recipient, listpolicy, sender)
    
    server.unbind()
    