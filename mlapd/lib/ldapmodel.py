import os.path
import ConfigParser
import ldap


CONFIG_FILE = os.path.dirname(__file__) + "/../etc/ldapmodel.conf"
ACCEPT_ACTION = "OK"
DEFER_ACTION = "DEFER_IF_PERMIT Service temporarily unavailable"
REJECT_ACTION = "REJECT Not Authorized"


class Modeler:        
    def __init__(self):
        self.config = ConfigParser.SafeConfigParser()
        self.config.readfp(open(CONFIG_FILE))
    
        __URL = self.config.get("LDAP_SERVER", "URL")
        
        self.server = ldap.initialize(__URL)
        
        __BINDDN = self.config.get("LDAP_SERVER", "BINDDN")
        __BINDPWD = self.config.get("LDAP_SERVER", "BINDPWD")        
        
        if __BINDDN != "":
            self.server.simple_bind(__BINDDN, __BINDPWD)
        
        self.ROOTDN = self.config.get("LDAP_SERVER", "ROOTDN")
    
    
    def __get_list_policy(self, listname):        
        self.config.set("LDAP_DATA", "recipient", listname)
        
        baseDN = self.ROOTDN
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
                    if sender in addresses:
                        return ACCEPT_ACTION
                    else:
                        return REJECT_ACTION
                else:
                    return REJECT_ACTION
            elif listpolicy == "internals":
                authorized_submitters = self.__get_list_authorized(listdn, listname, True)
                if authorized_submitters != None:
                    addresses = set(authorized_submitters)
                    if sender in addresses:
                        return ACCEPT_ACTION
                    else:
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
