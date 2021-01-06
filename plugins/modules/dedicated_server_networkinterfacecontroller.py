#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
---
module: dedicated_server_networkinterfacecontroller
short_description: Retrieve the mac addresses of the dedicated server
description:
    - This module retrieves the public or private mac address
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service_name
    link_type:
        required: true
        description: The link type, public or private (vrack)

'''

EXAMPLES = '''
synthesio.ovh.dedicated_server_networkinterfacecontroller:
  link_type: "private"
  service_name: "{{ service_name }}"
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
        link_type=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    link_type = module.params['link_type']
    service_name = module.params['service_name']
    try:
        result = client.get('/dedicated/server/%s/networkInterfaceController?linkType=%s' % (service_name, link_type))

        module.exit_json(changed=False, msg=result)
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
