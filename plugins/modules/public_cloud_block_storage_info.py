#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = r'''
---
module: public_cloud_block_storage_info

short_description: Retrieve OVH API for public cloud volume info.

description:
    - This module provides volume information on OVH public Cloud.

requirements:
    - ovh >= 0.5.0

options:
    service_name:
        required: true
        description: The service_name
    region:
        required: true
        description: The region where to deploy the volume
    name:
        required: true
        description: The Volume name
    image_id:
        required: false
        description: The id of the image/os to deploy on the volume
    snapshot_id:
        required: false
        description: snapshot id
'''

EXAMPLES = r'''
- name: Get Volume Info
  synthesio.ovh.public_cloud_block_storage_info:
    service_name: "{{ ovh_project_id }}"
    endpoint: "{{ ovh_endpoint }}"
    region: "{{ ovh_region }}"
    name: "{{ inventory_hostname }}-storage"
    application_key: "{{ ovh_application_key }}"
    application_secret: "{{ ovh_application_secret }}"
    consumer_key: "{{ ovh_consumer_key }}"
    volume_id: "{{ volume_id }}"
  delegate_to: localhost
  register: block_storage_metadata
'''

RETURN = r''' # '''

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
        region=dict(required=True),
        name=dict(required=True),
        image_id=dict(required=False),
        snapshot_id=dict(required=False),
        volume_id=dict(required=True),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    service_name = module.params['service_name']
    volume_id = module.params['volume_id']
    region = module.params['region']
    name = module.params['name']
    image_id = module.params['image_id']
    snapshot_id = module.params['snapshot_id']

    try:
        result = client.get('/cloud/project/%s/volume/%s' % (service_name, volume_id),
                             imageId=image_id,
                             name=name,
                             region=region,
                             snapshotId=snapshot_id,
                             )
        module.exit_json(
            msg="Volume {} ({}), has been created on OVH public Cloud".format(
                name, result['id']),
            changed=True,
            **result)

    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
