from __future__ import (absolute_import, division, print_function)

import urllib

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: ip_firewall_rule
short_description: Manage an OVH firewall rule for a given IP
description:
    - Manage an OVH firewall rule for a given IP
author: Marco Sarti
requirements:
    - ovh >= 0.5.0
options:
    ip:
        required: true
        description: The OVH ip
    ip_on_firewall:
        required: true
        description: The ip address on which firewall rule is applied
    sequence:
        required: true
        type: int
        description:
          - The sequence number that determines the order of the firewall rule.
          - Must be an integer between 0 and 19, inclusive.
          - Each rule must have a unique sequence number; attempting to reuse an existing one will result in an error.
    action:
        required: true
        description: The firewall rule action
        choices: ['deny','permit']
    protocol:
        required: true
        description: The firewall rule protocol
        choices: ['ah','esp','gre','icmp','ipv4','tcp','udp']
    destination_port:
        required: false
        description: Destination port for your rule. Only with TCP/UDP protocol
    source:
        required: false
        description: IPv4 CIDR notation of the source
    source_port:
        required: false
        description: Source port for your rule. Only with TCP/UDP protocol
    tcp_option:
        required: false
        type: dict
        default: {}
        description:
          - Additional TCP options for the firewall rule.
          - Only applicable when C(protocol) is set to C(tcp).
          - This is a dictionary with optional keys to define TCP-specific behavior.
        suboptions:
          fragments:
            description:
              - Whether to match fragmented packets.
            type: bool
            required: false
          option:
            description:
              - TCP flag condition to match.
              - Must be either C(established) or C(syn).
            type: str
            choices: ['established', 'syn']
            required: false
    state:
        required: false
        default: present
        choices: ['present','absent']
        description: Indicate the desired state
'''

EXAMPLES = r'''
- name: Open the HTTP port on address
  synthesio.ovh.ip_firewall_rule:
    ip: "192.0.2.1/24"
    ip_on_firewall: "192.0.2.1"
    state: present
    sequence: 0
    protocol: "tcp"
    destination_port: 80
    action: permit
  delegate_to: localhost
'''

RETURN = '''
msg:
    description: Message describing the result of the operation.
    type: str
    returned: always
    sample: Rule 0 is applied on 192.0.2.1
changed:
    description: Indicates whether any change was made.
    type: bool
    returned: always
    sample: true
'''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        ip=dict(required=True),
        ip_on_firewall=dict(required=True),
        sequence=dict(required=True, type="int"),
        action=dict(required=True),
        destination_port=dict(required=False, default=None),
        protocol=dict(choices=['ah', 'esp', 'gre', 'icmp', 'ipv4', 'tcp', 'udp'], required=True),
        source=dict(required=False, default=None),
        source_port=dict(required=False, default=None),
        state=dict(choices=['present', 'absent'], default='present'),
        tcp_option=dict(required=False, type='dict', default={})
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    ip = module.params['ip']
    ip_on_firewall = module.params['ip_on_firewall']
    sequence = module.params['sequence']
    action = module.params['action']
    destination_port = module.params['destination_port']
    protocol = module.params['protocol']
    source = module.params['source']
    source_port = module.params['source_port']
    state = module.params['state']
    tcp_option = module.params['tcp_option']

    if not (0 <= sequence <= 19):
        module.fail_json(msg="The 'sequence' parameter must be an integer between 0 and 19.")

    ip = urllib.parse.quote(ip, safe='')

    if module.check_mode:
        module.exit_json(
            msg="{} successfully {} on {} - (dry run mode)".format(
                ip, state, ip_on_firewall),
            changed=True)

    ips_on_firewall = client.wrap_call("GET", f"/ip/{ip}/firewall")

    if ip_on_firewall not in ips_on_firewall:
        module.fail_json(msg="A firewall must be created on IP before managing firewall rules.")

    rules = client.wrap_call("GET", f"/ip/{ip}/firewall/{ip_on_firewall}/rule")
    if sequence in rules:
        if state == 'absent':
            # Rule sequence exists and deletion is requested, we delete it
            client.wrap_call(
                "DELETE",
                f"/ip/{ip}/firewall/{ip_on_firewall}/rule/{sequence}"
            )
            module.exit_json(
                msg="Rule {} deleted on {}".format(sequence, ip_on_firewall), changed=True
            )
        else:
            # It is complicated to handle idempotence, the result of the GET does
            # not allow a comparison to verify whether there are changes in state or not.
            # So we refuse to insert rule with the same sequence.
            module.fail_json(
                msg=f"Rule with sequence {sequence} already exists. Please delete before using this sequence number."
            )
    elif state == 'absent':
        # No deletion needed
        module.exit_json(changed=False)

    # Rule sequence does not exist here, ok to create

    params = {
        "sequence": sequence,
        "action": action,
        "destinationPort": destination_port,
        "protocol": protocol,
        "source": source,
        "sourcePort": source_port,
        "tcpOption": tcp_option
    }
    filtered_params = {
        k: v for k, v in params.items()
        if v is not None and not (isinstance(v, dict) and not v)
    }
    client.wrap_call(
        "POST",
        f"/ip/{ip}/firewall/{ip_on_firewall}/rule",
        **filtered_params
    )
    module.exit_json(
        msg="Rule {} is applied on {}".format(sequence, ip_on_firewall), changed=True
    )


def main():
    run_module()


if __name__ == '__main__':
    main()
