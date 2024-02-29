#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = r'''
---
module: public_cloud_object_storage_policy

short_description: Manage OVH API for public cloud S3 bucket policy.

description:
    - This module applies a policy to an existing S3 user on a OVH public cloud bucket.

requirements:
    - ovh >= 0.5.0

options:
    service_name:
        required: true
        description: The service_name (OVH public cloud project ID)
    region:
        required: true
        description: The region where is located the S3 bucket
    name:
        required: true
        description: The S3 bucket name
    user_name:
        required: true
        description: The S3 user name (must already exists on public cloud project)
    policy:
        required: true
        description: Role associated to the user on this bucket
'''

EXAMPLES = r'''
- name: Add a read-only user to a S3 bucket
  synthesio.ovh.public_cloud_object_storage:
    service_name: "{{ service_name }}"
    region: "{{ region }}"
    name: "bucket-{{ inventory_hostname }}"
    user_name: "user-RaNdOm"
    policy: "readOnly"
  delegate_to: localhost
  register: object_storage_policy_metadata
'''

RETURN = r''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    """Apply a policy (user <-> role) to an OVH public cloud S3 bucket"""
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True),
        region=dict(required=True),
        name=dict(required=True),
        user_name=dict(required=True),
        policy=dict(required=True, choices=['deny', 'admin', 'readOnly', 'readWrite'])
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    service_name = module.params['service_name']
    region = module.params['region']
    name = module.params['name']
    user_name = module.params['user_name']
    policy = module.params['policy']

    if module.check_mode:
        module.exit_json(msg="Apply policy {} to user {} on S3 bucket {} ({}) - (dry run mode)".format(policy, user_name, name, region),
                         changed=True)

    user_list = []
    user_list = client.wrap_call("GET", f"/cloud/project/{service_name}/user")

    # Search user ID in cloud project existing users
    for user in user_list:
        if user['username'] == user_name:
            _ = client.wrap_call("POST", f"/cloud/project/{service_name}/region/{region}/storage/{name}/policy/{user['id']}",
                                 roleName=policy)
            module.exit_json(msg="Policy {} was applied to user {} on S3 bucket {} ({})".format(policy, user_name, name, region),
                             changed=True)

    module.fail_json(msg="User {} was not found on OVH public cloud project {}".format(user_name, service_name),
                     changed=False)


def main():
    run_module()


if __name__ == '__main__':
    main()
