#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = """
---
module: public_cloud_instance_flavor_change
short_description: Migrate an OVH public cloud instance to another flavor
description:
    - This migrate an OVH public cloud instance to another flavor
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service name
    instance_id:
        required: true
        description: The instance id
    flavor_id:
        required: true
        description: The flavor id
"""

EXAMPLES = r"""
- name: Get id for a flavor
  synthesio.ovh.public_cloud_flavorid_info:
    service_name: "{{ service_name }}"
    region: "GRA-7"
    name: "t1-45"
  delegate_to: localhost
  register: flavor_infos

- name: Change flavor for an instance
  synthesio.ovh.public_cloud_instance_flavor_change:
    instance_id: "{{ instance_id }}"
    service_name: "{{ service_name }}"
    flavor_id: "{{ flavor_infos.id }}"
  delegate_to: localhost
  when: flavor_infos.availability
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
            instance_id=dict(required=True),
            flavor_id=dict(required=True),
        )
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    client = OVH(module)

    service_name = module.params["service_name"]
    flavor_id = module.params["flavor_id"]
    instance_id = module.params["instance_id"]

    # Do the call
    client.wrap_call(
        "POST",
        f"/cloud/project/{service_name}/instance/{instance_id}/resize",
        flavorId=flavor_id,
    )

    module.exit_json(
        msg=f"Instance {instance_id} resized to {flavor_id}. This might take a couple of minutes.",
        changed=True,
    )


def main():
    run_module()


if __name__ == "__main__":
    main()
