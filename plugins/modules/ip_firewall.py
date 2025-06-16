from __future__ import (absolute_import, division, print_function)

import urllib

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: ip_firewall
short_description: Manage an OVH firewall for a given IP
description:
    - Manage an OVH firewall for a given IP
author: Marco Sarti
requirements:
    - ovh >= 0.5.0
options:
    ip:
        required: true
        description: The OVH ip
    ip_on_firewall:
        required: true
        description: The ip address on which firewall is applied
    enabled:
        required: false
        description: If you want this firewall enabled
        default: true
        choices: ['true','false']
    state:
        required: false
        default: present
        choices: ['present','absent']
        description: Indicate the desired state of firewall
'''

EXAMPLES = r'''
- name: Create a new disabled firewall
  synthesio.ovh.ip_firewall:
    ip: "192.0.2.1/24"
    ip_on_firewall: "192.0.2.1"
    state: present
    enabled: false
  delegate_to: localhost
'''

RETURN = ''' # '''


from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        ip=dict(required=True),
        ip_on_firewall=dict(required=True),
        enabled=dict(required=False, default=True, type="bool"),
        state=dict(choices=['present', 'absent'], default='present')
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    ip = module.params['ip']
    ip_on_firewall = module.params['ip_on_firewall']
    enabled = module.params['enabled']
    state = module.params['state']

    ip = urllib.parse.quote(ip, safe='')

    if module.check_mode:
        module.exit_json(
            msg="{} succesfully {} on {} - (dry run mode)".format(
                ip, state, ip_on_firewall),
            changed=True)

    ips_on_firewall = client.wrap_call("GET", f"/ip/{ip}/firewall")

    if ip_on_firewall in ips_on_firewall:
        current_fw = client.wrap_call("GET", f"/ip/{ip}/firewall/{ip_on_firewall}")
        if state == 'absent':
            client.wrap_call("DELETE", f"/ip/{ip}/firewall/{ip_on_firewall}")
            module.exit_json(changed=True)
        if current_fw['enabled'] == enabled:
            module.exit_json(changed=False)
    else:
        # The firewall does not exist in this ip_on_firewall
        if state == 'absent':
            module.exit_json(changed=False)
        else:
            client.wrap_call("POST",
                             f"/ip/{ip}/firewall",
                             ipOnFirewall=ip_on_firewall)

    client.wrap_call("PUT", f"/ip/{ip}/firewall/{ip_on_firewall}", enabled=enabled)

    module.exit_json(
        msg="Firewall applied on {}".format(ip_on_firewall), changed=True
    )


def main():
    run_module()


if __name__ == '__main__':
    main()
