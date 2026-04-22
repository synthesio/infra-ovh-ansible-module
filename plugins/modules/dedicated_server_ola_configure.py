#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
---
module: dedicated_server_ola_configure
short_description: Configure all network interfaces in OLA mode
description:
    - Configure all network interfaces in an OVHcloud Link Aggregation mode to switch to full network private mode (vrack)
author: OVHcloud Professional Services
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: OVHcloud name of the server
    aggregate_name:
        required: false
        default: "bond"
        description: Name of the aggregate

'''

EXAMPLES = '''
- name: Configure all network interfaces in OLA mode
    synthesio.ovh.dedicated_server_ola_configure:
        service_name: "ns12345.ip-1-2-3.eu"
        aggregate_name: "bond"
    delegate_to: localhost
    register: ola_config_task
'''

RETURN = '''
    task:
        description: OVHcloud task ID
        type: integer
'''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True),
        aggregate_name=dict(required=False, default="bond")
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    service_name = module.params['service_name']
    aggregate_name = module.params['aggregate_name']

    if module.check_mode:
        module.exit_json(msg=f"OLA configuration in progress on {service_name} with aggregate name {aggregate_name} - (dry run mode)", changed=True)

    virtualNetworkInterfaces = list()

    macaddresses = client.wrap_call('GET', f'/dedicated/server/{service_name}/networkInterfaceController')
    if len(macaddresses) >= 2:
        for macaddress in macaddresses:
            uuid = client.wrap_call('GET', f'/dedicated/server/{service_name}/networkInterfaceController/{macaddress}')
            virtualNetworkInterfaces.append(uuid['virtualNetworkInterface'])
        # Remove duplicate entries for Baremetal servers with 4 NICs
        virtualNetworkInterfaces = list(set(virtualNetworkInterfaces))
    else:
        module.fail_json(msg=f"{service_name} doesn't have enough interfaces eligible to OLA, please remove vRack association or Additional IPs")

    for virtualNetworkInterface in virtualNetworkInterfaces:
        vrack = client.wrap_call('GET', f'/dedicated/server/{service_name}/virtualNetworkInterface/{virtualNetworkInterface}')
        if vrack['vrack'] is not None:
            module.fail_json(msg=f"{vrack['name']} on {service_name} is linked to a vRack, please remove vRack association first")

    task = client.wrap_call('POST', f'/dedicated/server/{service_name}/ola/aggregation',name=aggregate_name, virtualNetworkInterfaces=virtualNetworkInterfaces)

    module.exit_json(msg=f"OLA configuration in progress on {service_name} with name {aggregate_name} !", changed=True, task=task)


def main():
    run_module()


if __name__ == '__main__':
    main()
