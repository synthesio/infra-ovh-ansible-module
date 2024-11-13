#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = """
---
module: public_cloud_instance_starting
short_description: Manage on or off status of an OVH public cloud instance
description:
    - This module manage on or off status of an OVH public cloud instance.
author: Alessandro Franci <alex@the-root.org>
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service name
    instance_id:
        required: true
        description: The instance id
    onoff_state:
        required: true
        choices: ["on", "off"]
        description: The on or off desired status
"""

EXAMPLES = r"""
- name: Start the instance
  synthesio.ovh.public_cloud_instance_shelving:
    instance_id: "{{ instance_id }}"
    service_name: "{{ service_name }}"
    onoff_state: "on"
 delegate_to: localhost

- name: Stop the instance
  synthesio.ovh.public_cloud_instance_shelving:
    instance_id: "{{ instance_id }}"
    service_name: "{{ service_name }}"
    onoff_state: "off"
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
        dict(
            service_name=dict(required=True),
            onoff_state=dict(required=True, choices=["on", "off"]),
            instance_id=dict(required=True),
        )
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    client = OVH(module)

    service_name = module.params["service_name"]
    onoff_state = module.params["onoff_state"]
    instance_id = module.params["instance_id"]

    # Set the route depending on the action
    if onoff_state == "on":
        route = f"/cloud/project/{service_name}/instance/{instance_id}/start"
    elif onoff_state == "off":
        route = f"/cloud/project/{service_name}/instance/{instance_id}/stop"
    else:
        module.fail_json(msg=f"On-Off state {onoff_state} is unknown", changed=False)

    # Do the call
    client.wrap_call("POST", route)

    message = f"State change to {onoff_state} for instance {instance_id}. This might take a couple of minutes."

    module.exit_json(
        result=message,
        changed=True,
    )


def main():
    run_module()


if __name__ == "__main__":
    main()