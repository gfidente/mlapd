### what it is ###

MLAPD is a mailing list access manager which uses LDAP to check for user's rights to post messages. It's designed to work in conjunction with [Postfix](http://www.postfix.org) as an Access Policy Delegation daemon. MLAPD manages mailing lists posting accesses and its goal is to read the data from LDAP, it listens on a TCP socket and can be queried concurrently by multiple Postfix instances.

### how it works ###

MLAPD is written in [Python](http://www.python.org) and depends only on the standard Python environment **plus** the [Python-LDAP module](http://python-ldap.sourceforge.net/); it shouldn't be invasive.

### details ###

MLAPD parses sender/receiver addresses from Postfix's incoming connections and gives back actions in return of a customizable lookup. The datasource is independent from the TCP server, includes LDAP support only but in theory others can be implemented.

There are some deployment details and notes about the integration of MLAPD in the wiki.

### contact ###

This project was migrated from Google Code in March 2015, but it wasn't updated for years when there. It probably works in a similarily old environment, but it definitely needs some love (and restructuring).

There is a [mailing list](http://groups.google.com/group/mlapd) you could use and an [issue tracker](https://github.com/gfidente/mlapd/issues) too.