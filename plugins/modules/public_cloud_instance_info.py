#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_instance_info
short_description: Retrieve all info for a OVH public cloud instance
description:
    - This module retrieves all info from a OVH public cloud instance
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service_name
    instance_id:
        required: true
        description: The instance uuid

'''

EXAMPLES = '''
synthesio.ovh.public_cloud_instance_info:
  instance_id: "{{ instance_id }}"
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
        instance_id=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    instance_id = module.params['instance_id']
    service_name = module.params['service_name']
    try:
        result = client.get('/cloud/project/%s/instance/%s' % (service_name, instance_id))

        module.exit_json(changed=False, **result)
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
