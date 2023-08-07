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
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import ovh_api_connect, ovh_argument_spec

try:
    from ovh.exceptions import APIError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False


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
    client = ovh_api_connect(module)

    service_name = module.params['service_name']
    aggregate_name = module.params['aggregate_name']

    if module.check_mode:
        module.exit_json(msg="OLA configuration in progress on {} with aggregate name {} - (dry run mode)"
                         .format(service_name, aggregate_name), changed=True)

    virtualNetworkInterfaces = list()

    try:
        macaddresses = client.get('/dedicated/server/%s/networkInterfaceController' % service_name)
        if len(macaddresses) >= 2:
            for macaddress in macaddresses:
                uuid = client.get('/dedicated/server/%s/networkInterfaceController/%s' % (service_name, macaddress))
                virtualNetworkInterfaces.append(uuid['virtualNetworkInterface'])
        else:
            module.fail_json(msg="{} doesn't have enough interfaces eligible to OLA, please remove vRack association or Additional IPs"
                             .format(service_name))
    except APIError as api_error:
        return module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    try:
        for virtualNetworkInterface in virtualNetworkInterfaces:
            vrack = client.get('/dedicated/server/%s/virtualNetworkInterface/%s' % (service_name, virtualNetworkInterface))
            if vrack['vrack'] is not None:
                module.fail_json(msg="{} on {} is linked to a vRack, please remove vRack association first".format(vrack['name'], service_name))
    except APIError as api_error:
        return module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    try:
        task = client.post('/dedicated/server/%s/ola/aggregation' % service_name,
                           name=aggregate_name, virtualNetworkInterfaces=virtualNetworkInterfaces)

        module.exit_json(msg="OLA configuration in progress on {} with name {} !".format(service_name, aggregate_name), changed=True, task=task)

    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
