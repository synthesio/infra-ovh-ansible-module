#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_users_info
short_description: Retrieve info for all OVH public cloud users
description:
    - This module retrieves info from all OVH public cloud users
author: Jonathan Piron <jonathan@piron.at>
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service_name

'''

EXAMPLES = '''
synthesio.ovh.public_cloud_users_info:
  service_name: "{{ service_name }}"
delegate_to: localhost
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    service_name = module.params['service_name']
    result = client.wrap_call("GET",
                              f"/cloud/project/{service_name}/user")
    module.exit_json(changed=False, results=result)


def main():
    run_module()


if __name__ == '__main__':
    main()
