#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type


DOCUMENTATION = '''
---
module: public_cloud_project_info
short_description: Get OVH Public cloud project SSH Key information
description:
    - This module retrieves SSH Key information from Public Cloud Project using a human readable ssh name (name)
author: Article714 (C. Guychard)
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description:
            - The ID of project
    ssh_key_name:
        required: true
        description:
            - The SSH Key humane-readable name
'''

EXAMPLES = '''
- name: "Get info on OVH public cloud SSH key {{ name }} "
  synthesio.ovh.public_cloud_project_info:
    project_name: "{{ id_project }}"
    ssh_key_name: "{{ ssh_key_name }}"
'''

RETURN = ''' All SSH Key information '''


from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import ovh_api_connect, ovh_argument_spec

try:
    from ovh.exceptions import APIError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        ssh_key_name=dict(required=True),
        service_name=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    ssh_key_name = module.params['ssh_key_name']
    service_name = module.params['service_name']

    key_ssh_list = []
    try:
        key_ssh_list = client.get('/cloud/project/{0}/sshkey'.format(service_name))
    except APIError as api_error:
        module.fail_json(msg="Error getting ssh key list: {0}".format(api_error))

    for ssh_data in key_ssh_list:

        if ssh_data['name'] == ssh_key_name:
            module.exit_json(changed=False, **ssh_data)

    module.fail_json(msg="Error: could not find given SSH Key name {0} in {1}".format(ssh_key_name, key_ssh_list))


def main():
    run_module()


if __name__ == '__main__':
    main()
