#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = r'''
---
module: public_cloud_block_storage_volume_info
short_description: Retrieve OVH API public cloud volume info by volume name.
description:
    - This module provides volume information for all instances in a Project.
Author: James Bos (GoDoo Pty Ltd)

requirements:
    - ovh >= 0.5.0

options:
    service_name:
        required: true
        description: Project ID
    region:
        required: true
        description: Region where volume is hosted
    name:
        required: true
        description: Volume name
'''

EXAMPLES = r'''
- name: Get Volume Info
  synthesio.ovh.public_cloud_block_storage_volume_info:
    service_name: "{{ ovh_project_id }}"
    endpoint: "{{ ovh_endpoint }}"
    region: "{{ ovh_region }}"
    name: "{{ inventory_hostname }}-storage"
    application_key: "{{ ovh_application_key }}"
    application_secret: "{{ ovh_application_secret }}"
    consumer_key: "{{ ovh_consumer_key }}"
  delegate_to: localhost
  register: block_storage_metadata
'''

RETURN = r''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True),
        region=dict(required=True),
        name=dict(required=True),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    service_name = module.params['service_name']
    region = module.params['region']

    try:
        result = client.wrap_call(
            'GET',
            '/cloud/project/%s/volume' % service_name,
            region=region,
        )

        # OVH API currently does not allow to filter by volume name
        result = [volume for volume in result if volume['name'] == module.params['name']][0]
        module.exit_json(changed=False, **result)

    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
