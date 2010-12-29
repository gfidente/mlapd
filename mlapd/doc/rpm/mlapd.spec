# Variables
%define name mlapd
%define version 0.3.3

# Preamble
Summary: MLAPD is a Mailing List access manager for Postfix which uses LDAP to check for user's rights to post messages.
Name: %{name}
Version: %{version}
Release: 2
License: GPL
Group: Applications/Internet
Packager: Mrugesh Karnik <mrugesh@brainfunked.org>
URL: http://code.google.com/p/%{name}/
Source0: http://%{name}.googlecode.com/files/%{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}/
BuildArch: noarch
Requires: python >= 2.4
Requires: python-ldap >= 2.2.0

%description
MLAPD is a Mailing List access manager which uses LDAP to check for
user's rights to post messages. It's designed to work in conjunction
with Postfix as an Access Policy Delegation daemon.

MLAPD manages electronic mail lists posting accesses. Its goal is to
read this kind of data from an LDAP server. It works as an Access
Policy Delegation agent for Postfix, so it listens on a TCP socket and
can be queried concurrently by multiple Postfix instances.

MLAPD is written in Python and it's supposed to offer good performances
under heavy loads, because it listens on a multithreaded TCP socket and
does not need to be spawned as a Postfix Content Filter every time.

%prep
%setup -q

%build

%install
rm -rf %{buildroot}

# Install the script
mkdir -pv %{buildroot}/%{_sbindir}
cp sbin/mlapd.py %{buildroot}/%{_sbindir}/%{name}

# Install the config file
mkdir -pv %{buildroot}/etc/%{name}
cp etc/ldapmodel.conf %{buildroot}/etc/%{name}/ldapmodel.conf

# Install the init script and its config file
mkdir -pv %{buildroot}/etc/init.d %{buildroot}/etc/sysconfig
cp doc/rpm/mlapd.rc %{buildroot}/etc/init.d/%{name}
cp doc/rpm/mlapd.sysconfig %{buildroot}/etc/sysconfig/%{name}

# Create directories for pid and log
mkdir -pv %{buildroot}/var/run/%{name} %{buildroot}/var/log/%{name}

%clean
rm -rf %{buildroot}

%pre
/usr/sbin/groupadd -r mlapd &>/dev/null || :
/usr/sbin/useradd -r -s /sbin/nologin -d / -g mlapd mlapd &>/dev/null || :

%post
/sbin/chkconfig --add %{name}

%preun
# Check if this is the last mlapd package to be uninstalled
if [ "$1" == 0 ]; then
	/sbin/service mlapd stop
	/sbin/chkconfig --del mlapd
fi

%files
%defattr(644, root, root, 755)
%doc doc/AUTHORS doc/COPYING doc/INSTALL doc/README doc/rpm/mlapd.spec
%attr(755, root, root) %{_sbindir}/%{name}
%attr(755, root, root) /etc/init.d/%{name}
%config /etc/sysconfig/%{name}
%config %attr(640, root, %{name}) /etc/%{name}/ldapmodel.conf
%dir %attr(775, root, %{name}) /var/run/%{name}
%dir %attr(775, root, %{name}) /var/log/%{name}
%dir %attr(775, root, %{name}) /etc/%{name}

%changelog
* Wed Dec 29 2010 Giulivo Navigante <giulivo.navigante@gmail.com> - 0.3.3-2
- directory /etc/mlapd added to the %dir section in %files
* Sat Dec 11 2010 Giulivo Navigante <giulivo.navigante@gmail.com> - 0.3.2-1
- Commited
* Thu May 13 2010 Mrugesh Karnik <mrugesh@brainfunked.org> - 0.3.1-1
- Initial RPM release.
