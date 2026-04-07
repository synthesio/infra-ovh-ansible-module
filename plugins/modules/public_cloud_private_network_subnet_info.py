#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_private_network_subnet_info
short_description: Get subnets of an OVHcloud Public Cloud private network
description:
  - Fetch the list of subnets attached to a private network.
requirements:
  - python-ovh >= 0.5.0
options:
  service_name:
    description: Public cloud project ID.
    required: true
    type: str
  network_id:
    description: Private network ID.
    required: true
    type: str
author:
  - Jonathan Piron <jonathan@piron.at>
'''

EXAMPLES = r'''
- name: Get all subnets of a private network
  synthesio.ovh.public_cloud_private_network_subnet_info:
    service_name: "{{ project_id }}"
    network_id: "{{ network_id }}"
  register: subnets_info
'''

RETURN = '''
subnets:
  description: List of subnet properties.
  returned: success
  type: list
  elements: dict
'''


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True, type="str"),
        network_id=dict(required=True, type="str"),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )
    client = OVH(module)

    service_name = module.params["service_name"]
    network_id = module.params["network_id"]

    subnets = client.wrap_call(
        "GET",
        f"/cloud/project/{service_name}/network/private/{network_id}/subnet",
    )

    module.exit_json(changed=False, subnets=subnets)


def main():
    run_module()


if __name__ == '__main__':
    main()
