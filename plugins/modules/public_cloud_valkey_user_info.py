#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_valkey_user_info
short_description: Get details of users on an OVHcloud Managed Valkey cluster
description:
  - Fetch the properties of all users on a Managed Valkey cluster.
requirements:
  - python-ovh >= 0.5.0
options:
  service_name:
    description: Public cloud project ID.
    required: true
    type: str
  cluster_id:
    description: Valkey cluster ID (UUID).
    required: true
    type: str
author:
  - Synthesio SRE Team
'''

EXAMPLES = r'''
- name: Get all users on a Valkey cluster
  synthesio.ovh.public_cloud_valkey_user_info:
    service_name: "{{ project_id }}"
    cluster_id: "{{ cluster_id }}"
  register: users_info
'''

RETURN = '''
users:
  description: List of user properties.
  returned: success
  type: list
  elements: dict
'''


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True, type="str"),
        cluster_id=dict(required=True, type="str"),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )
    client = OVH(module)

    service_name = module.params["service_name"]
    cluster_id = module.params["cluster_id"]

    user_ids = client.wrap_call(
        "GET",
        f"/cloud/project/{service_name}/database/valkey/{cluster_id}/user",
    )
    users = [
        client.wrap_call("GET", f"/cloud/project/{service_name}/database/valkey/{cluster_id}/user/{uid}")
        for uid in user_ids
    ]

    module.exit_json(changed=False, users=users)


def main():
    run_module()


if __name__ == '__main__':
    main()
