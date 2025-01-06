#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type
DOCUMENTATION = """
---
module: dedicated_server_ip_info
short_description: Retrieve IP specifications for an OVH dedicated server
description:
    - This module retrieves detailed IP specifications for an OVH dedicated server
author: David Harkis
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service_name
"""
EXAMPLES = r"""
- name: Retrieve IP specifications for an OVH dedicated server
  synthesio.ovh.dedicated_server_ip_info:
    service_name: "{{ service_name }}"
  delegate_to: localhost
  register: ip_info
"""
RETURN = r"""
ipv4:
    description: Orderable IP v4 details.
    returned: always
    type: list
    elements: dict
    contains:
        blockSizes:
            description: Orderable IP blocks sizes.
            type: list
            elements: int
            sample: [1, 4, 8, 16, 32, 64, 128]
        included:
            description: Are those IP included with your offer.
            type: bool
            sample: true
        ipNumber:
            description: Total number of IP that can be routed to this server.
            type: int
            sample: 256
        number:
            description: Total number of prefixes that can be routed to this server.
            type: int
            sample: 254
        optionRequired:
            description: Which option is required to order this type of IP.
            type: str
            choices: [professionalUse]
        type:
            description: This IP type.
            type: str
            choices: [failover, static, unshielded]
            sample: failover
ipv6:
    description: Orderable IP v6 details.
    returned: always
    type: list
    elements: dict
    contains:
        blockSizes:
            description: Orderable IP blocks sizes.
            type: list
            elements: int
            choices: [1, 4, 8, 16, 32, 64, 128, 256]
        included:
            description: Are those IP included with your offer.
            type: bool
        ipNumber:
            description: Total number of IP that can be routed to this server.
            type: int
        number:
            description: Total number of prefixes that can be routed to this server.
            type: int
        optionRequired:
            description: Which option is required to order this type of IP.
            type: str
            choices: [professionalUse]
        type:
            description: This IP type.
            type: str
            choices: [failover, static, unshielded]"""
from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import (
    OVH,
    ovh_argument_spec,
)


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(service_name=dict(required=True)))
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        module.exit_json(changed=False)

    client = OVH(module)
    service_name = module.params["service_name"]
    result = client.wrap_call(
        "GET", f"/dedicated/server/{service_name}/specifications/ip"
    )
    module.exit_json(changed=False, **result)


def main():
    run_module()


if __name__ == "__main__":
    main()
