#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: vps_info
short_description: Retrieve all info for a OVH vps
description:
    - This module retrieves all info for a OVH vps
author: Maxime Dupré / Paul Tap (armorica)
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service_name
'''

EXAMPLES = r'''
- name: Retrieve all info for an OVH vps
  synthesio.ovh.vps_info:
    service_name: "{{ service_name }}"
  delegate_to: localhost
  register: dedicated_info
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
    result = client.wrap_call("GET", f"/vps/{service_name}")

    module.exit_json(changed=False, **result)


def main():
    run_module()


if __name__ == '__main__':
    main()
