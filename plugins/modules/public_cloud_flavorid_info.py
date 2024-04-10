#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = r"""
---
module: public_cloud_flavorid_info
short_description: Get flavor id, and its availability, based on commercial name
description:
    - Get flavorId based on commercial name (t1-45, b2-7 etc) with its availability
    - The flavorId change between region
    - The retrieved flavorId can be used to spawn a new instance
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    name:
        required: true
        description: The commercial name of the flavor (t1-45, b2-7 etc)
    region:
        required: true
        description: The region where to lookup for flavorId
    service_name:
        required: true
        description: The service_name

"""

EXAMPLES = r"""
- name: Get flavor id
  synthesio.ovh.public_cloud_flavorid_info:
    service_name: "{{ service_name }}"
    region: "GRA7"
    name: "t1-45"
  delegate_to: localhost
  register: flavor_infos
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
            name=dict(required=True),
            region=dict(required=True),
        )
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    client = OVH(module)

    service_name = module.params["service_name"]
    name = module.params["name"]
    region = module.params["region"]

    result = client.wrap_call("GET", f"/cloud/project/{service_name}/flavor", region=region)
    for f in result:
        if f["name"] == name:
            flavor_id = f["id"]
            available = f["available"]
            module.exit_json(changed=False, id=flavor_id, availability=available)

    module.fail_json(
        msg="Flavor {} not found in {}".format(name, region), changed=False
    )


def main():
    run_module()


if __name__ == "__main__":
    main()
