#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
---
module: dedicated_server_ola_unconfigure
short_description: Unconfigure all network interfaces in OLA mode
description:
    - Unconfigure all private network interfaces in an OVHcloud Link Aggregation mode to switch to default network mode
author: OVHcloud Professional Services
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: OVHcloud name of the server

'''

EXAMPLES = '''
- name: Unconfigure all network interfaces in OLA mode
    synthesio.ovh.dedicated_server_ola_unconfigure:
        service_name: "ns12345.ip-1-2-3.eu"
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
        service_name=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    service_name = module.params['service_name']

    if module.check_mode:
        module.exit_json(msg="OLA unconfiguration in progress on {} - (dry run mode)".format(service_name),changed=True)

    try:
        macaddresses = client.get('/dedicated/server/%s/networkInterfaceController?linkType=private_lag' % service_name)
        if len(macaddresses) > 0:
            uuid = client.get('/dedicated/server/%s/networkInterfaceController/%s' % (service_name, macaddresses[0]))
        else:
            module.fail_json(msg="{} doesn't seems to have OLA configured, please check again".format(service_name))
    except APIError as api_error:
        return module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    try:
        task = client.post('/dedicated/server/%s/ola/reset' % service_name, virtualNetworkInterface=uuid['virtualNetworkInterface'])

        module.exit_json(msg="OLA unconfiguration in progress on {} !".format(service_name), changed=True, task=task)

    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
