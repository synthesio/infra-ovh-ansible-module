#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type
DOCUMENTATION = """
---
module: dedicated_server_network_info
short_description: Retrieve network specifications for an OVH dedicated server
description:
    - This module retrieves detailed network specifications for an OVH dedicated server
author: David Harkis
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service_name
"""
EXAMPLES = r"""
- name: Retrieve network specifications for an OVH dedicated server
  synthesio.ovh.dedicated_server_network_info:
    service_name: "{{ service_name }}"
  delegate_to: localhost
  register: network_info
"""
RETURN = r"""
bandwidth:
    description: Bandwidth details.
    returned: always
    type: dict
    contains:
        InternetToOvh:
            description: Bandwidth limitation Internet to OVH.
            type: dict
            contains:
                unit:
                    description: Bandwidth unit.
                    type: str
                    sample: Mbps
                value:
                    description: Bandwidth value.
                    type: int
                    sample: 1000
        OvhToInternet:
            description: Bandwidth limitation OVH to Internet.
            type: dict
            contains:
                unit:
                    description: Bandwidth unit.
                    type: str
                    sample: Mbps
                value:
                    description: Bandwidth value.
                    type: int
                    sample: 1000
        OvhToOvh:
            description: Bandwidth limitation OVH to OVH.
            type: dict
            contains:
                unit:
                    description: Bandwidth unit.
                    type: str
                    sample: Mbps
                value:
                    description: Bandwidth value.
                    type: int
                    sample: 1000
        type:
            description: Bandwidth offer type.
            type: str
            choices: [improved, included, platinum, premium, standard, ultimate]
            sample: included
connection:
    description: Network connection flow rate.
    returned: always
    type: dict
    contains:
        unit:
            description: Flow rate unit.
            type: str
            sample: Mbps
        value:
            description: Flow rate value.
            type: int
            sample: 25000
ola:
    description: OLA details.
    returned: always
    type: dict
    contains:
        available:
            description: Is the OLA feature available.
            type: bool
            sample: true
        availableModes:
            description: What modes are supported.
            type: list
            elements: dict
            contains:
                default:
                    description: Is this the default mode.
                    type: bool
                    sample: true
                interfaces:
                    description: Network interfaces configuration.
                    type: list
                    elements: dict
                    contains:
                        aggregation:
                            description: Is aggregation enabled.
                            type: bool
                            sample: true
                        count:
                            description: Number of interfaces.
                            type: int
                            sample: 2
                        type:
                            description: Interface type.
                            type: str
                            sample: public
                name:
                    description: Mode name.
                    type: str
                    sample: public(2)+private(2)
        supportedModes:
            description: Supported modes.
            type: list
            elements: str
            sample: ["vrack_aggregation"]
routing:
    description: Routing details.
    returned: always
    type: dict
    contains:
        ipv4:
            description: IPv4 routing details.
            type: dict
            contains:
                gateway:
                    description: IPv4 gateway.
                    type: str
                    sample: 100.64.0.1
                ip:
                    description: IPv4 address.
                    type: str
                    sample: 57.129.64.192
                network:
                    description: IPv4 network.
                    type: str
                    sample: 57.129.64.0/24
        ipv6:
            description: IPv6 routing details.
            type: dict
            contains:
                gateway:
                    description: IPv6 gateway.
                    type: str
                    sample: fe80:0000:0000:0000:0000:0000:0000:0001
                ip:
                    description: IPv6 address.
                    type: str
                    sample: 2001:41d0:070f:c000:0000:0000:0000:0000/56
                network:
                    description: IPv6 network.
                    type: str
                    sample: 2001:41d0:70f::0000/48
switching:
    description: Switching details.
    returned: always
    type: dict
    contains:
        name:
            description: Switch name.
            type: str
            sample: fra1-lim3-unettor99a-n93
traffic:
    description: Traffic details.
    returned: always
    type: dict
    contains:
        inputQuotaSize:
            description: Monthly input traffic quota allowed.
            type: dict
        inputQuotaUsed:
            description: Monthly input traffic consumed this month.
            type: dict
        isThrottled:
            description: Is bandwidth throttled for being over quota.
            type: bool
            sample: false
        outputQuotaSize:
            description: Monthly output traffic quota allowed.
            type: dict
        outputQuotaUsed:
            description: Monthly output traffic consumed this month.
            type: dict
        resetQuotaDate:
            description: Next reset quota date for traffic counter.
            type: str
vmac:
    description: VMAC information for this dedicated server.
    returned: always
    type: dict
    contains:
        quota:
            description: Maximum number of VirtualMacs allowed on this server.
            type: int
            sample: 32
        supported:
            description: Server is compatible with vmac or not.
            type: bool
            sample: true
vrack:
    description: vRack details.
    returned: when configured
    type: dict
    contains:
        bandwidth:
            description: vRack bandwidth limitation.
            type: dict
            contains:
                unit:
                    description: Bandwidth unit.
                    type: str
                    sample: Mbps
                value:
                    description: Bandwidth value.
                    type: int
                    sample: 25000
        type:
            description: Bandwidth offer type.
            type: str
            choices: [included, standard]
            sample: standard"""
from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import (
    OVH,
    ovh_argument_spec,
)


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(service_name=dict(required=True)))
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        module.exit_json(changed=False)

    client = OVH(module)
    service_name = module.params["service_name"]
    result = client.wrap_call(
        "GET", f"/dedicated/server/{service_name}/specifications/network"
    )
    module.exit_json(changed=False, **result)


def main():
    run_module()


if __name__ == "__main__":
    main()
