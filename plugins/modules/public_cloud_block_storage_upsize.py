#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = r'''
---
module: public_cloud_block_storage_upsize
short_description: Extend OVH public cloud volume.
description:
    - This module extends a volume on OVH public cloud.
author: James Bos (GoDoo Ptd Ltd)

requirements:
    - ovh >= 0.5.0

options:
    service_name:
        required: true
        description: Project ID
    region:
        required: true
        description: Region where volume is hosted
    volume_id:
        required: true
        description: The volume id
    size:
        required: true
        description: Volume size (in GB)
        type: integer
    name:
        required: true
        description: Volume name
'''

EXAMPLES = r'''
- name: Resize Volume
  synthesio.ovh.public_cloud_block_storage_upsize:
    volume_id: "{{ volume_metadata.id }}"
    service_name: "{{ ovh_project_id }}"
    endpoint: "{{ ovh_endpoint }}"
    region: "{{ ovh_region }}"
    size: "{{ storage_gb }}"
    name: "{{ inventory_hostname }}-storage"
    application_key: "{{ ovh_application_key }}"
    application_secret: "{{ ovh_application_secret }}"
    consumer_key: "{{ ovh_consumer_key }}"
  delegate_to: localhost
  register: volume_metadata
'''

RETURN = r''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True),
        region=dict(required=True),
        size=dict(required=True, type="int"),
        name=dict(required=True),
        volume_id=dict(required=True),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    service_name = module.params['service_name']
    volume_id = module.params['volume_id']
    region = module.params['region']
    size = module.params['size']
    name = module.params['name']

    try:
        result = client.wrap_call(
                "POST",
                '/cloud/project/%s/volume/%s/upsize' % (service_name, volume_id),
                name=name,
                region=region,
                size=size,
            )
        module.exit_json(
            msg="Volume {} ({}), has been resized on OVH public Cloud".format(
                name, result['id']),
            changed=True,
            **result)

    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
