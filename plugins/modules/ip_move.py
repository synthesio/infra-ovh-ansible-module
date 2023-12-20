#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: ip_move
short_description: Move IP to another service
description:
    - Move IP to another service
author: Erwan Ben Souiden
requirements:
    - ovh >= 0.5.0
options:
    ip:
        required: true
        description: The ip
    service_name:
        required: true
        description: The service_name
'''

EXAMPLES = r'''
- name: Modify reverse on IP
  synthesio.ovh.ip_move:
    ip: 192.0.2.1
    service_name: "nsXXXXX.ip-YY-YYY-YYY.net"
  delegate_to: localhost
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import ovh_api_connect, ovh_argument_spec
import urllib.parse

try:
    from ovh.exceptions import APIError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        ip=dict(required=True),
        service_name=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    ip = module.params['ip']
    service_name = module.params['service_name']

    result = {}
    try:
        result = client.get('/ip/%s' % (ip))
    except APIError as api_error:
        return module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    try:
        current_service_name = result['routedTo']['serviceName']
    except KeyError:
        current_service_name = ''

    if current_service_name == service_name:
        module.exit_json(msg="{} already moved to {} !".format(ip, service_name), changed=False)

    try:
        if module.check_mode:
            module.exit_json(msg="Move {} to {} done ! - (dry run mode)".format(ip, service_name), changed=True)

        client.post(
            '/ip/%s/move' % (ip),
            nexthop=None,
            to=service_name
        )

        module.exit_json(msg="{} successfully moved to {} !".format(ip, service_name), changed=True)
    except APIError as api_error:
        return module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
