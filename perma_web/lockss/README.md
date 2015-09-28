# LOCKSS Installation Instructions

## Add LOCKSS repo:
    
    $ sudo yum install yum-utils
    $ sudo yum-config-manager --add-repo http://www.lockss.org/repo/
    $ sudo rpm --import http://www.lockss.org/LOCKSS-GPG-RPM-KEY

## Install packages:

    $ sudo yum install -y lockss-daemon java-1.8.0-openjdk-headless.x86_64 ntp 

## Enable services:

    $ sudo chkconfig --add lockss
    $ sudo chkconfig lockss on
    $ sudo chkconfig ntpd on
    
## Make LOCKSS storage dir:

    $ sudo mkdir -p /srv/caches/cache0
    
## Lock down SSH by subnet:

(If not handled by router/firewall.)

## Open LOCKSS ports:

    $ sudo iptables -I INPUT 1 -m state --state NEW -m tcp -p tcp --dport 8081 -j ACCEPT
    $ sudo iptables -I INPUT 1 -m state --state NEW -m tcp -p tcp --dport 8082 -j ACCEPT
    $ sudo iptables -I INPUT 1 -m state --state NEW -m tcp -p tcp --dport 9729 -j ACCEPT

## Configure LOCKSS daemon:

    $ sudo /etc/lockss/hostconfig
    root is configuring
    eth0: error fetching interface information: Device not found
    LOCKSS host configuration for Linux.
    For more information see /etc/lockss/README
    Configuring for user lockss
    Fully qualified hostname (FQDN) of this machine: [hlslpermamirror.law.harvard.edu]
    IP address of this machine: [] <daemon ip>
    Is this machine behind NAT?: [N]
    Initial subnet for admin UI access: [140.247.203.0/24] <admin subnet>
    LCAP V3 protocol port: [9729]
    PROXY port: [8080]
    Admin UI port: [8081]
    Mail relay for this machine: [localhost]
    Does mail relay localhost need user & password: [N]
    E-mail address for administrator: [] <admin email>
    Path to java: [/usr/bin/java] <something like /usr/java/jre1.8.0_60/bin/java>
    Java switches: []
    Configuration URL: [http://props.lockss.org:8001/daemon/lockss.xml] https://perma.cc/lockss/daemon_settings.txt
    Verify configuration server authenticity?: [Y]
    Server certificate keystore: [lockss-ca] /etc/lockss/perma-test.keystore
    Configuration proxy (host:port): [NONE]
    Preservation group(s): [prod] perma
    Content storage directories: [] /srv/caches/cache0
    Temporary storage directory: [/srv/caches/cache0/tmp]
    User name for web UI administration: [] lockss
    Password for web UI administration user lockss: []
    Password for web UI administration (again): []
    
    Configuration:
    ...
    OK to store this configuration: [Y]
    
## Import Perma server certificate:

    sudo keytool -importkeystore -srckeystore /etc/lockss/perma-test.keystore -destkeystore /usr/lib/jvm/java-1.8.0-openjdk-1.8.0.60-2.b27.el7_1.x86_64/jre/lib/security/cacerts
    
## Start daemon:

    sudo service lockss start
    
## Subscribe to Perma Archival Units:

- Go to Journal Configuration.
- Click Add AUs.

(TODO: remove necessity to do this?)
    
## Further reading:

- http://plnwiki.lockss.org/wiki/index.php/LOCKSS_Technical_Manual#How_to_install_and_configure_a_locks_daemon_on_a_PLN_node.3F
- http://webcache.googleusercontent.com/search?q=cache:EdUEEhW-jsYJ:metaarchive.org/public/ddp/chapters/Hea-Fen-Pit-2_2.doc+&cd=4&hl=en&ct=clnk&gl=us
- http://www.lockss.org/docs/LOCKSS-Linux-Install.pdf