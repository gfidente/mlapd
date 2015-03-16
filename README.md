MLAPD is a mailing list access manager which uses LDAP to check for user's rights to post messages. It's designed to work in conjunction with [Postfix](http://www.postfix.org) as an Access Policy Delegation daemoA.

### what it is ###

MLAPD manages mailing lists posting accesses. Its goal is to read the data from LDAP. It works as an [Access Policy Delegation](http://www.postfix.org/SMTPD_POLICY_README.html) agent for Postfix, listens on a TCP socket and can be queried concurrently by multiple Postfix instances.

### how it works ###

MLAPD is written in [Python](http://www.python.org) and requires on the standard Python environment **plus** the [Python-LDAP module](http://python-ldap.sourceforge.net/); it shouldn't be invasive.

### details ###

MLAPD parses sender/receiver addresses from Postfix's incoming connections and gives back actions in return of a customizable lookup. The datasource is independent from the TCP server, includes LDAP support only but in theory others can be implemented.

There are some deployment details and notes about the integration of MLAPD with third party applications in the wiki.

### contact ###

There is a [mailing list](http://groups.google.com/group/mlapd) you could use and an [issue tracker](https://github.com/gfidente/mlapd/issues) too.