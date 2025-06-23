#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_user_s3credentials
short_description: Manage s3 credentials for an OVH public cloud user
description:
    - This module manages s3 credentials for an OVH public cloud user
author: Jonathan Piron <jonathan@piron.at>
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description:
            - The service_name
    user_id:
        required: true
        description: The user_id to manage s3 credentials force
    access:
        required: false
        description: The access to delete. Required with state: absent
    state:
        required: false
        default: present
        choices: ['present', 'absent']
        description: Indicate the desired state of the S3 credential

'''

EXAMPLES = '''
synthesio.ovh.public_cloud_user_s3credentials:
  service_name: "{{ service_name }}"
  user_id: "{{ user_id }}"
delegate_to: localhost
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, OVHResourceNotFound, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True),
        user_id=dict(required=True),
        access=dict(required=False, default=None),
        state=dict(choices=['present', 'absent'], default='present')
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    service_name = module.params['service_name']
    user_id = module.params['user_id']
    access = module.params['access']
    state = module.params['state']

    if state == 'absent':
        if access is None:
            module.fail_json(msg="access is required with state: absent")
        try:
            access = client.wrap_call("GET",
                                      f"/cloud/project/{service_name}/user/{user_id}/s3Credentials/{access}")
        except OVHResourceNotFound:
            module.exit_json(changed=False)
        else:
            client.wrap_call("DELETE",
                             f"/cloud/project/{service_name}/user/{user_id}/s3Credentials/{access}")
            module.exit_json(changed=True)
    else:
        credentials = client.wrap_call("POST",
                                       f'/cloud/project/{service_name}/user/{user_id}/s3Credentials')
        module.exit_json(changed=True, **credentials)


def main():
    run_module()


if __name__ == '__main__':
    main()
