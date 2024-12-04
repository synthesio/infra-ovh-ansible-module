#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: dedicated_server_specification_hardware
short_description: Retrieve all hardware specification for a OVH dedicated server
description:
    - This module retrieves all hardware information for a OVH dedicated server
author: Saul Bertuccio
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service_name
'''

EXAMPLES = r'''
- name: Retrieve all hardwared information for an OVH dedicated server
  synthesio.ovh.dedicated_server_info:
    service_name: "{{ service_name }}"
  delegate_to: localhost
  register: dedicated_hardware
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec

def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    service_name = module.params['service_name']
    result = client.wrap_call("GET", f"/dedicated/server/{service_name}/specifications/hardware")

    module.exit_json(changed=False, **result)


def main():
    run_module()


if __name__ == '__main__':
    main()
