import os.path
import ConfigParser
import ldap

ACCEPT_ACTION = "OK"
DEFER_ACTION = "DEFER_IF_PERMIT Service temporarily unavailable"
REJECT_ACTION = "REJECT Not Authorized"

CONFIG_FILE = os.path.dirname(__file__) + "/ldapmdl.conf"

class Modeler:    
    def __init__(self):
        self.config = ConfigParser.SafeConfigParser()
        self.config.readfp(open(CONFIG_FILE))
    
        self.__URL = self.config.get("LDAP_SERVER", "URL")
        self.server = ldap.initialize(self.__URL)
        
        self.__BINDDN = self.config.get("LDAP_SERVER", "BINDDN")
        self.__BINDPWD = self.config.get("LDAP_SERVER", "BINDPWD")        
        if self.__BINDDN != "":
            self.server.simple_bind(self.__BINDDN, self.__BINDPWD)
        
        self.__ROOTDN = self.config.get("LDAP_SERVER", "ROOTDN")
    
    
    def __get_list_policy(self, listname):
        """Return the policy used on a list
        
        Parameters:
            listname is the mailing list rfc822 address
        """
        
        self.config.set("LDAP_DATA", "recipient", listname)
        
        baseDN = self.__ROOTDN
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = [self.config.get("LDAP_DATA", "POLICYATTR")]
        searchFilter = self.config.get("LDAP_DATA", "LISTFILTER")
    
        # server.set_option(ldap.sizelimit, 1)
        results_id = self.server.search(baseDN, searchScope, searchFilter, retrieveAttributes)
        while True:
            result_type, result_data = self.server.result(results_id, 0)
            if (result_data == []):
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_dn, result_set = result_data[0]
                    for attribute in retrieveAttributes:
                        return result_dn, result_set[attribute][0]
                        
    
    def __get_list_authorized(self, listdn, listname):
        """Return a list of authorized addresses
        
        Parameters:
            listdn is the ldapdn of listname
            listname is the mailing list rfc822 address
        """
        
        self.config.set("LDAP_DATA", "recipient", listname)
        
        baseDN = listdn
        searchScope = ldap.SCOPE_BASE
        retrieveAttributes = [self.config.get("LDAP_DATA", "ALLWDATTRIBUTE")]
        searchFilter = self.config.get("LDAP_DATA", "LISTFILTER")
    
        # server.set_option(ldap.sizelimit, 1)
        results_id = self.server.search(baseDN, searchScope, searchFilter, retrieveAttributes)
        while True:
            result_type, result_data = self.server.result(results_id, 0)
            if (result_data == []):
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_dn, result_set = result_data[0]
                    for attribute in retrieveAttributes:
                        return result_set[attribute]

    
    def __get_action(self, listname, sender):
        """Return the action for Postfix!
        
        Parameters:
            listname is the mailing list rfc822 address
            sender is the submitter rfc822 address
        """
        
        listdn, listpolicy = self.__get_list_policy(listname)
        
        if listpolicy == "open":
            return ACCEPT_ACTION
        elif listpolicy == "domain":
            senderdomain = sender.split("@")[1]
            listdomain = listname.split("@")[1]
            if listdomain == senderdomain :
                return ACCEPT_ACTION
            else:
                return REJECT_ACTION
        elif listpolicy == "filter":
            authorized = False
            authorized_submitters = self.__get_list_authorized(listdn, listname)
            for address in authorized_submitters:
                if address.find(sender) != -1:
                    authorized = True
            if authorized:
                return ACCEPT_ACTION
            else:
                return REJECT_ACTION
    
    
    def handle_data(self, map):
        """Main method of the modeler,
        takes a map from the protocol connection and returns the action
        
        Parameters:
            map is of type {key:value} and contains the Postfix data
        """

        if map.has_key("sender") and map.has_key("recipient"):
            sender = map["sender"]
            senderdomain = sender.split("@")[1]
            recipient = map["recipient"]
            action = self.__get_action(recipient, sender)
            self.server.unbind()
            return action
        else:
            return DEFER_ACTION