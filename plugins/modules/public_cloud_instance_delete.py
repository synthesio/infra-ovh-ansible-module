#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = """
---
module: public_cloud_instance_delete
short_description: Manage OVH API for public cloud instance deletion
description:
    - This module manage the deletion of an instance on OVH public Cloud
    - The instance must not be ACTIVE to be deletd
author: Andreas Trawoeger <atrawog@dorgeln.org>
requirements:
    - ovh >= 0.5.0
options:
    name:
        required: true
        description:
            - The instance name to delete
    service_name:
        required: true
        description:
            - The service_name
    region:
        required: true
        description:
            - The region where the instance is deployed
    force_delete:
        required: false
        description:
            - Force the instance deletion even if it is not in ACTIVE status


"""

EXAMPLES = """
- name: "Delete instance of {{ inventory_hostname }} on public cloud OVH"
  synthesio.ovh.public_cloud_instance_delete:
    name: "{{ inventory_hostname }}"
    service_name: "{{ service_name }}"
    region: "{{ region }}"
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
            name=dict(required=True),
            service_name=dict(required=True),
            region=dict(required=True),
            force_delete=dict(required=False, default=False)
        )
    )
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    client = OVH(module)

    name = module.params["name"]
    service_name = module.params["service_name"]
    region = module.params["region"]
    force_delete = module.params["force_delete"]

    instances_list = client.wrap_call(
        "GET", f"/cloud/project/{service_name}/instance", region=region
    )

    for i in instances_list:

        if i["name"] == name:
            instance_id = i["id"]
            instance_details = client.wrap_call(
                "GET", f"/cloud/project/{service_name}/instance/{instance_id}"
            )
            if instance_details["status"] == "ACTIVE" and not force_delete:
                module.fail_json(msg="Instance must not be active to be deleted", changed=False)

    client.wrap_call(
        "DELETE", f"/cloud/project/{service_name}/instance/{instance_id}"
    )
    module.exit_json(changed=True)


def main():
    run_module()


if __name__ == "__main__":
    main()
