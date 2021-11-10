#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_ip_failover_by_ip
short_description: Retrieve failover Id from an IP
description:
    - This module retrieves failover Id from its IP
author: Article714 (C. Guychard)
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service_name
    ip:
        required: true
        description: IP of failover
'''

EXAMPLES = '''
synthesio.ovh.public_cloud_instance_info_by_name:
    service_name: "{{ service_name }}"
    ip: "{{ ip }}"
delegate_to: localhost
'''

RETURN = ''' failover Id '''

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
        ip=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    service_name = module.params['service_name']
    ip = module.params['ip']

    try:
        instances_list = client.get('/cloud/project/{0}/ip/failover'.format(service_name))
    except APIError as api_error:
        module.fail_json(msg="Error getting failover list: {0}".format(api_error))

    for inst in instances_list:

        failoverId=None
        if inst['ip'] == ip:
          failoverId = inst['id']
        if failoverId:
            module.exit_json(changed=False, **inst)

    module.fail_json(changed=False, msg="Errort: Could not find ip {0}".format(ip))

def main():
    run_module()


if __name__ == '__main__':
    main()