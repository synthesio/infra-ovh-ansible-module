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

RETURN = '''
creationDate:
    description: User creation date.
    type: date-time
    returned: always
    sample: 2025-12-15T14:30:47.592Z
description:
    description: User description.
    type: string
    returned: always
    sample: test-user
id:
    description: User id.
    type: int
    returned: always
    sample: 599859
openstackId:
    description: User id on openstack.
    type: string
    returned: always
    sample: xxx
password:
    description: User password.
    type: string
    returned: always
    sample: 6664jq8gs6aZtbxxVtRbRqYKkfG7xyYN
roles:
    description: User roles.
    type: list of role
    returned: always
    sample:
        [{
            "description": "string",
            "id": "string",
            "name": "string",
            "permissions": [
                "string"
            ]
        }]
username:
    description: Username.
    type: str
    returned: always
    sample: user-wKbTguqcnX4Z
status:
    description: User status.
    type: enum (creating┃deleted┃deleting┃ok)
    returned: always
    sample: creating
msg:
    description: Message indicating the result of the operation.
    type: str
    returned: always
    sample: User was created on OVH public cloud
changed:
    description: Indicates if any change was made.
    type: bool
    returned: always
    sample: true
'''

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
            if module.check_mode:
                user = client.wrap_call("GET",
                                        f"/cloud/project/{service_name}/user/{user_id}")
            else:
                client.wrap_call("DELETE",
                                 f"/cloud/project/{service_name}/user/{user_id}")
        except OVHResourceNotFound:
            module.exit_json(changed=False)
        else:
            module.exit_json(changed=True)
    else:
        if not module.check_mode:
            user = client.wrap_call("POST",
                                    f"/cloud/project/{service_name}/user",
                                    role=role,
                                    description=description,
                                    roles=roles)
            module.exit_json(msg="User was created on OVH public cloud", changed=True, **user)
        else:
            module.exit_json(msg="User was created on OVH public cloud - (dry run mode)", changed=True)


def main():
    run_module()


if __name__ == '__main__':
    main()
