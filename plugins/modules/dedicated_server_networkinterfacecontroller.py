#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
---
module: dedicated_server_networkinterfacecontroller
short_description: Retrieve the mac addresses of the dedicated server
description:
    - This module retrieves the public or private mac address
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service name
    link_type:
        required: true
        description: The link type
            - public or public_lag
            - private or private_lag (vrack)
            - provisioning or provisioning_lag
            - isolated (OVHcloud special mode)
'''

EXAMPLES = r'''
- name: Retrieve the mac addresses of the dedicated server
  synthesio.ovh.dedicated_server_networkinterfacecontroller:
    link_type: "private"
    service_name: "{{ service_name }}"
  delegate_to: localhost
  register: dedicated_macaddress
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True),
        link_type=dict(required=False)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    link_type = None
    if module.params['link_type']:
        link_type = module.params['link_type']
    service_name = module.params['service_name']

    # Return all mac addresses
    if not link_type:
        result = client.wrap_call("GET", f"/dedicated/server/{service_name}/networkInterfaceController")

    # Return only specific type mac addresses
    elif link_type:
        result = client.wrap_call("GET", f"/dedicated/server/{service_name}/networkInterfaceController?linkType={link_type}")
        # XXX: This is a hack, would be better to detect what kind of server you are using:
        # If there is no result, maybe you have a server with multiples network interfaces on the same link (2x public + 2x vrack), like HGR
        # In this case, retry with public_lag/private_lag linkType
        if not result:
            result = client.wrap_call("GET", f"/dedicated/server/{service_name}/networkInterfaceController?linkType={link_type}_lag")

    module.exit_json(changed=False, msg=result)


def main():
    run_module()


if __name__ == '__main__':
    main()
