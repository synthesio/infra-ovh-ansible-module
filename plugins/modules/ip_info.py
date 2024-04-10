#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: ip_info
short_description: Retrieve all info for a given OVH IP
description:
    - Retrieve all info for a given OVH IP
author: Erwan Ben Souiden
requirements:
    - ovh >= 0.5.0
options:
    ip:
        required: true
        description: The ip
'''

EXAMPLES = r'''
- name: Get IP details
  synthesio.ovh.ip_info:
    ip: "192.0.2.1"
  register: ip_info
  delegate_to: localhost

- debug:
    msg: "{{ ip_info }}"

- debug:
    msg: "{{ ip_info['isAdditionalIp'] }}"
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        ip=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    ip = module.params['ip']
    result = client.wrap_call("GET", f"/ip/{ip}")

    module.exit_json(changed=False, **result)


def main():
    run_module()


if __name__ == '__main__':
    main()
