#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = """
---
module: dedicated_server_display_name
short_description: Modify the server display name in ovh manager
description:
    - Modify the server display name in ovh manager, to help you find your server with your own naming
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service name
    display_name:
        required: true
        description: The display name to set

"""

EXAMPLES = r"""
- name: "Set display name to {{ display_name }} on server {{ ovhname }}"
  synthesio.ovh.dedicated_server_display_name:
    service_name: "{{ ovhname }}"
    display_name: "{{ display_name }}"
  delegate_to: localhost
"""

RETURN = """ # """

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import (
    OVH,
    ovh_argument_spec,
)


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(
        dict(display_name=dict(required=True), service_name=dict(required=True))
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    client = OVH(module)

    display_name = module.params["display_name"]
    service_name = module.params["service_name"]

    if module.check_mode:
        module.exit_json(
            msg=f"display_name has been set to {display_name} ! - (dry run mode)",
            changed=True,
        )

    result = client.get(f"/dedicated/server/{service_name}/serviceInfos")

    service_id = result["serviceId"]
    resource = {"resource": {"displayName": display_name, "name": service_name}}
    client.put(f"/service/{service_id}", **resource)
    module.exit_json(
        msg=f"displayName succesfully set to {display_name} for {service_name} !",
        changed=True,
    )


def main():
    run_module()


if __name__ == "__main__":
    main()
