#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
---
module: dedicated_server_rescuesshkey
short_description: Set the ssh key for access in rescue mode
description:
    - Set the ssh key for access in rescue mode in a dedicated server
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service_name
    ssh_key:
        required: true
        description: The ssh public key string

'''

EXAMPLES = r'''
- name: "Set the ssh key for access in rescue mode {{ service_name }}"
  synthesio.ovh.dedicated_server_rescuesshkey:
    service_name: "{{ service_name }}"
    ssh_key: "ssh-ed25519 [....]"
  delegate_to: localhost
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True),
        ssh_key=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    service_name = module.params['service_name']
    ssh_key = module.params['ssh_key']

    if module.check_mode:
        module.exit_json(msg="Ssh key is set for {} - (dry run mode)".format(service_name), changed=True)

    server_state = client.wrap_call("GET", f"/dedicated/server/{service_name}")

    if server_state['rescueSshKey'] == ssh_key:
        module.exit_json(msg="Ssh key is already set on {}".format(service_name), changed=False)

    client.wrap_call("PUT", f"/dedicated/server/{service_name}", rescueSshKey=ssh_key)

    module.exit_json(msg="Ssh key is set on {}".format(service_name), changed=True)


def main():
    run_module()


if __name__ == '__main__':
    main()
