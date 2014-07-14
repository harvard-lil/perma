Stouts.iptables
===============

[![Build Status](https://travis-ci.org/Stouts/Stouts.iptables.png)](https://travis-ci.org/Stouts/Stouts.iptables)

Ansible role which manage iptables

#### Variables

THe role variables and default values.

```yaml
iptables_enabled: yes                   # The role is enabled
iptables_logging: yes                   # Log dropped packets

iptables_rule_path: /etc/iptables.rules # Path to rule file

iptables_allowed_tcp_ports: [22, 25, 80, 443] # List of allowed tcp ports
iptables_forwarded_tcp_ports: []        # Forward tcp ports
                                        # Ex. iptables_forwarded_tcp_ports:
                                        #       - { from: 22, to: 2222 }

iptables_allowed_udp_ports: []          # List of allowed udp ports
iptables_forwarded_udp_ports: []        # Ex. iptables_forwarded_udp_ports:
                                        #       - { from: 22, to: 2222 }

iptables_raw_rules: []                  # List of raw rules
                                        # Ex. iptables_raw_rules:
                                        #     - -A INPUT -i eth0 -p tcp -m tcp --dport 22 -j ACCEPT
                                        #     - -A INPUT -i eth0 -p tcp -m tcp --dport 80 -j ACCEPT
```

#### Usage

Add `Stouts.iptables` to your roles and setup the variables in your playbook file.
Example:

```yaml

- hosts: all

  roles:
    - Stouts.iptables

  vars:
    iptables_allowed_tcp_ports: [22]
    iptables_forwarded_tcp_ports:
    - {from: 22, to: 2222}
```

#### License

Licensed under the MIT License. See the LICENSE file for details.

#### Feedback, bug-reports, requests, ...

Are [welcome](https://github.com/Stouts/Stouts.iptables/issues)!
