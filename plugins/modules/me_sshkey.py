#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: me_sshkey
short_description: Retrieve ssh key by name
description:
    - This module retrieves a ssh key by its name
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    ssh_key_name:
        required: true
        description: The ssh key name
'''

EXAMPLES = r'''
- name: Retrieve ssh key by name
  synthesio.ovh.me_sshkey:
    ssh_key_name: "{{ ssh_key_name }}"
  delegate_to: localhost
  register: ssh_key

- name: "Set the ssh key for access in rescue mode {{ service_name }}"
  synthesio.ovh.dedicated_server_rescuesshkey:
    service_name: "{{ service_name }}"
    ssh_key: "{{ ssh_key.key }}"
  delegate_to: localhost
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        ssh_key_name=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    ssh_key_name = module.params['ssh_key_name']
    result = client.wrap_call("GET", f"/me/sshKey/{ssh_key_name}")

    module.exit_json(changed=False, **result)


def main():
    run_module()


if __name__ == '__main__':
    main()
