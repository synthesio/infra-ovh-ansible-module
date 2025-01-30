#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_user
short_description: Manage a OVH public cloud user
description:
    - This module manages a OVH public cloud user
author: Jonathan Piron <jonathan@piron.at>
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description:
            - The service_name
    role:
      required: false
      description:
          - the role to assign to the user
    roles:
      required: false
      description:
          - the roles to assign to the user
    description:
        required: false
    user_id:
        required: false
        description: The user_id to manage. Required with state: absent
    state:
        required: false
        default: present
        choices: ['present', 'absent']
        description: Indicate the desired state of the public cloud user

'''

EXAMPLES = '''
- name: "Create a user on public cloud OVH"
  synthesio.ovh.public_cloud_user:
    service_name: "{{ service_name }}"
    role: "{{ role }}"
    roles: "{{ roles }}"
    description: "{{ description }}"
  delegate_to: localhost
  register: user_creation

- name: "Wait for user creation completion"
  public_cloud_user_info:
    service_name: "{{ service_name }}"
    user_id: "{{ user_creation.json.id }}"
  delegate_to: localhost
  register: user_retrieval
  until: user_retrieval.status == "ok"
  retries: 6
  delay: 5
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, OVHResourceNotFound, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True),
        role=dict(required=False, default=None),
        roles=dict(required=False, default=None),
        description=dict(required=False, default=None),
        user_id=dict(required=False, default=None),
        state=dict(choices=['present', 'absent'], default='present')
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    service_name = module.params['service_name']
    role = module.params['role']
    roles = module.params['roles']
    description = module.params['description']
    user_id = module.params['user_id']
    state = module.params['state']

    if state == 'absent':
        if user_id is None:
            module.fail_json(msg="user_id is required with state: absent")
        try:
            client.wrap_call("DELETE",
                             f"/cloud/project/{service_name}/user/{user_id}")
        except OVHResourceNotFound:
            module.exit_json(changed=False)
        else:
            module.exit_json(changed=True)
    else:
        user = client.wrap_call("POST",
                                f"/cloud/project/{service_name}/user",
                                role=role,
                                description=description,
                                roles=roles)
        module.exit_json(msg="User was created on OVH public cloud", changed=True, **user)


def main():
    run_module()


if __name__ == '__main__':
    main()
