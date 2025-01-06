#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type
DOCUMENTATION = """
---
module: dedicated_server_hardware_info
short_description: Retrieve hardware specifications for an OVH dedicated server
description:
    - This module retrieves detailed hardware specifications for an OVH dedicated server
author: David Harkis
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service_name
"""
EXAMPLES = r"""
- name: Retrieve hardware specifications for an OVH dedicated server
  synthesio.ovh.dedicated_server_hardware_info:
    service_name: "{{ service_name }}"
  delegate_to: localhost
  register: hardware_info
"""
RETURN = r"""
bootMode:
    description: Server boot mode.
    returned: always
    type: str
    sample: uefi
coresPerProcessor:
    description: Number of cores per processor.
    returned: always
    type: int
    sample: 6
defaultHardwareRaidSize:
    description: Default hardware raid size for this server.
    returned: when configured
    type: dict
    contains:
        unit:
            description: Size unit.
            type: str
            sample: GB
        value:
            description: Size value.
            type: int
            sample: 1000
defaultHardwareRaidType:
    description: Default hardware raid type configured on this server.
    returned: when configured
    type: str
    choices: [raid0, raid1, raid10, raid1E, raid5, raid50, raid6, raid60]
description:
    description: Commercial name of this server.
    returned: when available
    type: str
    sample: ADVANCE-1 | AMD EPYC 4244P - AMD EPYC 4244P
diskGroups:
    description: Details about the groups of disks in the server.
    returned: always
    type: list
    elements: dict
    contains:
        defaultHardwareRaidSize:
            description: Default hardware raid size for this disk group.
            type: dict
            returned: when configured
        defaultHardwareRaidType:
            description: Default hardware raid type for this disk group.
            type: str
            returned: when configured
            choices: [raid0, raid1, raid10, raid1E, raid5, raid50, raid6, raid60]
        description:
            description: Human readable description of this disk group.
            type: str
            sample: 2 X Disk NVME 960 GB, JBOD
        diskGroupId:
            description: Identifier of this disk group.
            type: int
            sample: 1
        diskSize:
            description: Disk capacity.
            type: dict
            contains:
                unit:
                    description: Size unit.
                    type: str
                    sample: GB
                value:
                    description: Size value.
                    type: int
                    sample: 960
        diskType:
            description: Type of the disk.
            type: str
            sample: NVME
        numberOfDisks:
            description: Number of disks in this group.
            type: int
            sample: 2
        raidController:
            description: Raid controller managing this group of disks.
            type: str
expansionCards:
    description: Details about the server's expansion cards.
    returned: when present
    type: list
    elements: dict
    contains:
        description:
            description: Expansion card description.
            type: str
        type:
            description: Expansion card type.
            type: str
            choices: [fpga, gpu]
formFactor:
    description: Server form factor.
    returned: always
    type: str
    choices: [0.25u, 0.5u, 1u, 2u, 3u, 4u]
    sample: 0.5u
memorySize:
    description: RAM capacity.
    returned: always
    type: dict
    contains:
        unit:
            description: Size unit.
            type: str
            sample: MB
        value:
            description: Size value.
            type: int
            sample: 32768
motherboard:
    description: Server motherboard.
    returned: always
    type: str
    sample: S3661
numberOfProcessors:
    description: Number of processors in this dedicated server.
    returned: always
    type: int
    sample: 1
processorArchitecture:
    description: Processor architecture bit.
    returned: always
    type: str
    choices: [arm64, armhf32, ppc64, x86, x86-ht, x86_64]
    sample: x86_64
processorName:
    description: Processor name.
    returned: always
    type: str
    sample: Epyc4244P
threadsPerProcessor:
    description: Number of threads per processor.
    returned: always
    type: int
    sample: 12
usbKeys:
    description: Capacity of the USB keys installed on your server.
    returned: when present
    type: list
    elements: dict
    contains:
        unit:
            description: Size unit.
            type: str
            sample: GB
        value:
            description: Size value.
            type: int"""
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
        "GET", f"/dedicated/server/{service_name}/specifications/hardware"
    )
    module.exit_json(changed=False, **result)


def main():
    run_module()


if __name__ == "__main__":
    main()
