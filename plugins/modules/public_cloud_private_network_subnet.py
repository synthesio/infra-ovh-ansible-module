#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_private_network_subnet
short_description: Manage subnets in an OVHcloud Public Cloud private network
description:
  - Create or delete a subnet in an OVHcloud Public Cloud private network.
  - The subnet is identified by C(network) (CIDR) and C(region).
  - All fields are immutable after creation (no update endpoint exists in the API).
requirements:
  - python-ovh >= 0.5.0
options:
  service_name:
    description: Public cloud project ID.
    required: true
    type: str
  network_id:
    description: Private network ID.
    required: true
    type: str
  network:
    description:
      - Subnet CIDR (e.g. C(192.168.1.0/24)). Used together with C(region) to identify the subnet.
      - Required when creating a subnet.
    required: false
    type: str
  region:
    description:
      - Region where the subnet is created (e.g. C(GRA11)). Used together with C(network) to identify the subnet.
      - Required when creating a subnet.
    required: false
    type: str
  start:
    description: First IP address of the allocation pool (e.g. C(192.168.1.10)).
    required: false
    type: str
  end:
    description: Last IP address of the allocation pool (e.g. C(192.168.1.200)).
    required: false
    type: str
  dhcp:
    description: Enable DHCP on the subnet.
    required: false
    type: bool
  no_gateway:
    description: Do not allocate a default gateway IP.
    required: false
    type: bool
  state:
    description: Desired state of the subnet.
    choices: ['present', 'absent']
    default: present
    type: str
author:
  - Jonathan Piron <jonathan@piron.at>
'''

EXAMPLES = r'''
- name: Create a subnet
  synthesio.ovh.public_cloud_private_network_subnet:
    service_name: "{{ project_id }}"
    network_id: "{{ network_id }}"
    network: 192.168.1.0/24
    region: GRA11
    start: 192.168.1.10
    end: 192.168.1.200
    dhcp: true
    state: present

- name: Create a subnet without gateway
  synthesio.ovh.public_cloud_private_network_subnet:
    service_name: "{{ project_id }}"
    network_id: "{{ network_id }}"
    network: 10.0.0.0/24
    region: SBG5
    start: 10.0.0.10
    end: 10.0.0.250
    dhcp: false
    no_gateway: true
    state: present

- name: Delete a subnet
  synthesio.ovh.public_cloud_private_network_subnet:
    service_name: "{{ project_id }}"
    network_id: "{{ network_id }}"
    network: 192.168.1.0/24
    region: GRA11
    state: absent
'''

RETURN = ''' # '''


def _find_subnet(client, service_name, network_id, network, region):
    """Return the subnet dict matching the given CIDR and region, or None."""
    subnets = client.wrap_call(
        "GET",
        f"/cloud/project/{service_name}/network/private/{network_id}/subnet",
    )
    for subnet in subnets:
        if subnet.get("cidr") != network:
            continue
        for pool in subnet.get("ipPools", []):
            if pool.get("region") == region:
                return subnet
    return None


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True, type="str"),
        network_id=dict(required=True, type="str"),
        network=dict(required=False, type="str", default=None),
        region=dict(required=False, type="str", default=None),
        start=dict(required=False, type="str", default=None),
        end=dict(required=False, type="str", default=None),
        dhcp=dict(required=False, type="bool", default=None),
        no_gateway=dict(required=False, type="bool", default=None),
        state=dict(choices=["present", "absent"], default="present"),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        required_together=[("network", "region")],
        supports_check_mode=True,
    )
    client = OVH(module)

    service_name = module.params["service_name"]
    network_id = module.params["network_id"]
    network = module.params["network"]
    region = module.params["region"]
    state = module.params["state"]

    if not network or not region:
        module.fail_json(msg="'network' and 'region' are required")

    current = _find_subnet(client, service_name, network_id, network, region)

    # --- state: absent ---
    if state == "absent":
        if current is None:
            module.exit_json(changed=False, msg=f"Subnet '{network}' in '{region}' does not exist")

        subnet_id = current["id"]
        if module.check_mode:
            module.exit_json(
                changed=True,
                msg=f"Subnet '{network}' [{subnet_id}] in '{region}' would be deleted (dry run)",
            )

        client.wrap_call(
            "DELETE",
            f"/cloud/project/{service_name}/network/private/{network_id}/subnet/{subnet_id}",
        )
        module.exit_json(changed=True, msg=f"Subnet '{network}' [{subnet_id}] in '{region}' deleted")

    # --- state: present ---

    if current is not None:
        subnet_id = current["id"]
        module.exit_json(
            changed=False,
            msg=f"Subnet '{network}' [{subnet_id}] in '{region}' already exists",
            **current,
        )

    if module.check_mode:
        module.exit_json(
            changed=True,
            msg=f"Subnet '{network}' in '{region}' would be created (dry run)",
        )

    post_kwargs = dict(network=network, region=region)
    for param, api_field in [
        ("start", "start"),
        ("end", "end"),
        ("dhcp", "dhcp"),
        ("no_gateway", "noGateway"),
    ]:
        value = module.params.get(param)
        if value is not None:
            post_kwargs[api_field] = value

    result = client.wrap_call(
        "POST",
        f"/cloud/project/{service_name}/network/private/{network_id}/subnet",
        **post_kwargs,
    )
    module.exit_json(changed=True, msg=f"Subnet '{network}' in '{region}' created", **result)


def main():
    run_module()


if __name__ == '__main__':
    main()
