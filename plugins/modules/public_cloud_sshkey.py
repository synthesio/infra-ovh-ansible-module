#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_sshkey
short_description: Create a new ssh key for OVH public cloud
description:
    - This module manage creation of a new ssh key for OVH public cloud
author: Marco Sarti <m.sarti@onetag.com>
requirements:
    - ovh >= 0.5.0
options:
    name:
        required: true
        description:
            - The name of the ssh key to create
    public_key:
        required: true
        description:
            - The public key to upload
    region:
        required: false
        description:
            - The region where to deploy public key
    service_name:
        required: true
        description:
            - The service_name
'''

EXAMPLES = r'''
- name: "Create a new ssh key on public cloud OVH"
  synthesio.ovh.public_cloud_sshkey:
    name: "{{ sshkey_name }}"
    public_key: "{{ sshkey_public_key }}"
    service_name: "{{ service_name }}"
    region: "{{ region }}"
  delegate_to: localhost
  register: sshkey_data
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        name=dict(required=True),
        public_key=dict(required=True),
        region=dict(required=False, default=None),
        service_name=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    name = module.params['name']
    service_name = module.params['service_name']
    public_key = module.params['public_key']
    region = module.params['region']

    sshkey_list = client.wrap_call(
        "GET",
        f"/cloud/project/{service_name}/sshkey")

    for k in sshkey_list:

        if k['name'] == name:
            module.exit_json(changed=False,
                             msg="Key {} is already present".format(name))

    result = client.wrap_call("POST",
                              f"/cloud/project/{service_name}/sshkey",
                              name=name,
                              region=region,
                              publicKey=public_key
                              )

    module.exit_json(changed=True, **result)


def main():
    run_module()


if __name__ == '__main__':
    main()
