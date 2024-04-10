#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = r"""
---
module: public_cloud_private_network_info

short_description: Get information about private networks for a given region.

description:
    - Get the openstack id for a private network depending on the region.

requirements:
    - ovh >= 0.5.0

options:
    service_name:
        required: true
        description: The service name
    private_network:
        required: true
        description: The OVH private network
    region:
        required: true
        description: The region where to lookup for network
"""

EXAMPLES = r"""
  - name: Get the openstack id for the private network in the region
  synthesio.ovh.public_cloud_private_network_info:
    service_name: "{{ service_name }}"
    private_network: "{{ network }}"
    region: "GRA11"
  delegate_to: localhost
  register: network_info

"""

RETURN = r"""
openstack_id:
    description: Openstack alpha numeric identifier of the network
    returned: when matching region is found
    type: str
    sample: 54e97ee2-407c-4dbc-a833-39d2910514d4
# """

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import (
    OVH,
    ovh_argument_spec,
)


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(
        dict(
            service_name=dict(required=True),
            private_network=dict(required=True),
            region=dict(required=True),
        )
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    client = OVH(module)

    service_name = module.params["service_name"]
    private_network = module.params["private_network"]
    region = module.params["region"]

    network_list = client.wrap_call(
        "GET", f"/cloud/project/{service_name}/network/private/{private_network}"
    )

    for network in network_list["regions"]:
        if network["region"] == region:
            module.exit_json(changed=False, openstack_id=network["openstackId"])

    module.fail_json(msg=f"No network found for {region}", changed=False)


def main():
    run_module()


if __name__ == "__main__":
    main()
