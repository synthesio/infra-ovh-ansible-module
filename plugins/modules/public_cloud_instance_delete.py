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
    ovh_api_connect,
    ovh_argument_spec,
)

try:
    from ovh.exceptions import APIError

    HAS_OVH = True
except ImportError:
    HAS_OVH = False


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(
        dict(
            name=dict(required=True),
            service_name=dict(required=True),
            region=dict(required=True),
        )
    )
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    client = ovh_api_connect(module)

    name = module.params["name"]
    service_name = module.params["service_name"]
    region = module.params["region"]
    try:
        instances_list = client.get(
            "/cloud/project/%s/instance" % (service_name), region=region
        )
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    for i in instances_list:

        if i["name"] == name:
            instance_id = i["id"]
            instance_details = client.get(
                "/cloud/project/%s/instance/%s" % (service_name, instance_id)
            )

    try:
        result = client.delete(
            "/cloud/project/%s/instance/%s" % (service_name, instance_id)
        )
        module.exit_json(changed=True)
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == "__main__":
    main()
