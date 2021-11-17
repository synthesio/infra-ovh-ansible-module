#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_failover_ip_info
short_description: Retrieve all info for a OVH failover IP
description:
    - This module retrieves all info from a OVH failover IP
author: Article714 (M. Piriou, C. Guychard)
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The OVH API service_name is  Public cloud project Id
    fo_ip:
        required: true
        description:
            - The fail-over IP

'''

EXAMPLES = '''
synthesio.ovh.public_cloud_failover_ip_info:
  fo_ip: "{{ fo_ip }}"
  service_name: "{{ service_name }}"
delegate_to: localhost
register: fo_ip_id
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
        fo_ip=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    fo_ip = module.params['fo_ip']
    service_name = module.params['service_name']

    fo_ips_list = []
    try:
        fo_ips_list = client.get('/cloud/project/{0}/ip/failover'.format(service_name))
    except APIError as api_error:
        module.fail_json(msg="Error getting failover ips list: {0}".format(api_error))

    for ip_data in fo_ips_list:

        if ip_data['ip'] == fo_ip:
            module.exit_json(changed=False, **ip_data)

    module.fail_json(msg="Error: could not find given fail-over IP {0} in {1}".format(fo_ip, fo_ips_list))


def main():
    run_module()


if __name__ == '__main__':
    main()
