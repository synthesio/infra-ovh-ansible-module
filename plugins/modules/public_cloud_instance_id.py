#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = """
---
module: public_cloud_instance_id
short_description: Retrieve the id for a public cloud instance
description:
    - This module retrieves the id for a OVH public cloud instance
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service name
    instance_name:
        required: true
        description: The instance name
    region:
        required: true
        description:
          - The region where the instance is deployed

"""

EXAMPLES = r"""
- name: Get the id of a OVH public cloud instance
  synthesio.ovh.public_cloud_instance_info:
    instance_name: "{{ instance_id }}"
    service_name: "{{ service_name }}"
    region: "{{ region }}"
  delegate_to: localhost
  register: instance_id
"""

RETURN = r"""
id:
    description: Id of a public cloud instance
    type: str
    sample: kai1hei3-2aku-cz2h-pkc9-aapo1jeigh9e
"""

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import (
    OVH,
    ovh_argument_spec,
)


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(
        dict(
            service_name=dict(required=True),
            instance_name=dict(required=True),
            region=dict(required=True),
        )
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    client = OVH(module)

    instance_name = module.params["instance_name"]
    service_name = module.params["service_name"]
    region = module.params["region"]

    instance_id = False

    # Get instance id
    instances_list = client.wrap_call(
        "GET", f"/cloud/project/{service_name}/instance", region=region
    )
    for instance in instances_list:
        if instance["name"] == instance_name:
            instance_id = instance["id"]

    # Exit if no instance were found
    if not instance_id:
        module.fail_json(
            msg=f"No instance {instance_name} found in {region}", changed=False
        )

    module.exit_json(id=instance_id, changed=False)


def main():
    run_module()


if __name__ == "__main__":
    main()
