#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = """
---
module: public_cloud_instance_info_by_name
short_description: Retrieve instance Id from a human-readable name
description:
    - This module retrieves instance Id from its human-readable name
author: Article714 (C. Guychard)
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The OVH API service_name is  Public cloud project Id
    instance_name:
        required: true
        description: The instance human-readable name
    region:
        required: true
        description:
            - The region where to deploy the instance

"""

EXAMPLES = """
synthesio.ovh.public_cloud_instance_info_by_name:
  instance_name: "{{ instance_name }}"
  service_name: "{{ service_name }}"
  region: "{{ region_name }}"
delegate_to: localhost
"""

RETURN = """ Instance Id """

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
            service_name=dict(required=True),
            instance_name=dict(required=True),
            region=dict(required=True),
        )
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    client = ovh_api_connect(module)

    instance_name = module.params["instance_name"]
    service_name = module.params["service_name"]
    a_region = module.params["region"]

    try:
        instances_list = client.get(
            "/cloud/project/{0}/instance".format(service_name), region=a_region
        )
    except APIError as api_error:
        module.fail_json(msg="Error getting instances list: {0}".format(api_error))

    for inst in instances_list:

        instanceId = None
        if inst["name"] == instance_name:
            instanceId = inst["id"]
        if instanceId:
            module.exit_json(changed=False, **inst)

    module.fail_json(
        changed=False,
        msg="Errort: Could not find instance named {0}".format(instance_name),
    )


def main():
    run_module()


if __name__ == "__main__":
    main()
