#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = """
---
module: vps_info
short_description: Retrieve all info for a OVH vps
description:
    - This module retrieves all info for a OVH vps
author: Maxime Dupré / Paul Tap (armorica)
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service name
"""

EXAMPLES = r"""
- name: Retrieve all info for an OVH vps
  synthesio.ovh.vps_info:
    service_name: "{{ service_name }}"
  delegate_to: localhost
  register: vps_info
"""

RETURN = """ # """

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import (
    OVH,
    collection_module,
)


@collection_module(dict(service_name=dict(required=True)))
def main(module: AnsibleModule, client: OVH, service_name: str):
    result = client.wrap_call("GET", f"/vps/{service_name}")

    module.exit_json(changed=False, **result)


if __name__ == "__main__":
    main()
