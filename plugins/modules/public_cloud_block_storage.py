#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = r'''
---
module: public_cloud_block_storage

short_description: Manage OVH API for public cloud volume.

description:
    - This module manage volume creation/deletion on OVH public Cloud.

requirements:
    - ovh >= 0.5.0

options:
    service_name:
        required: true
        description: The service_name
    region:
        required: true
        description: The region where to deploy the volume
    size:
        required: true
        description: Volume size (in GB)
        type: integer
    volume_type:
        required: true
        default: classic
        description: Volume type
        choices: [ 'classic', 'high-speed', 'high-speed-gen2']
    name:
        required: true
        description: The Volume name
    description:
        required: false
        description: Volume description
    image_id:
        required: false
        description: The id of the image/os to deploy on the volume
    snapshot_id:
        required: false
        description: snapshot id
    state:
        required: false
        default: present
        choices: ['present','absent']
        description: Indicate the desired state of volume
'''

EXAMPLES = r'''
- name: Ensure Volume is state wanted
  synthesio.ovh.public_cloud_block_storage:
    service_name: "{{ service_name }}"
    region: "{{ region }}"
    size: "{{ size }}"
    name: "volume-{{ inventory_hostname }}"
    description: "Data Volume of {{ size }}"
    volume_type: "{{ volume_type }}"
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
        size=dict(required=True, type="int"),
        volume_type=dict(required=False, choices=['classic', 'high-speed', 'high-speed-gen2'], default='classic'),
        name=dict(required=True),
        description=dict(required=False),
        image_id=dict(required=False),
        snapshot_id=dict(required=False),
        state=dict(choices=['present', 'absent'], default='present')
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    service_name = module.params['service_name']
    region = module.params['region']
    size = module.params['size']
    volume_type = module.params['volume_type']
    name = module.params['name']
    description = module.params['description']
    image_id = module.params['image_id']
    snapshot_id = module.params['snapshot_id']
    state = module.params['state']

    if module.check_mode:
        module.exit_json(msg="Ensure volume {} is {} - (dry run mode)".format(name, state),
                         changed=True)

    volume_list = []
    try:
        volume_list = client.get('/cloud/project/%s/volume' % service_name,
                                 region=region
                                 )

    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))  # show error message and exit

    # Search if the volume exist. Consider you manage a strict nomenclature based on name.
    for volume in volume_list:
        if volume['name'] == name:
            volume_id = volume['id']
            volume_details = client.get('/cloud/project/%s/volume/%s' % (service_name, volume_id))
            if state == 'absent':
                try:
                    _ = client.delete('/cloud/project/%s/volume/%s' % (service_name, volume_id))
                    module.exit_json(
                        msg="Volume {} ({}), has been deleted from cloud".format(
                            name, volume_id),
                        changed=True)

                except APIError as api_error:
                    module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

            else:  # state == 'present':
                module.exit_json(
                    msg="Volume {} ({}) has already been created on OVH public Cloud ".format(
                        name, volume_id),
                    changed=False,
                    **volume_details)

    if state == 'present':
        try:
            result = client.post('/cloud/project/%s/volume' % service_name,
                                 description=description,
                                 imageId=image_id,
                                 name=name,
                                 region=region,
                                 size=size,
                                 snapshotId=snapshot_id,
                                 type=volume_type
                                 )
            module.exit_json(
                msg="Volume {} ({}), has been created on OVH public Cloud".format(
                    name, result['id']),
                changed=True,
                **result)

        except APIError as api_error:
            module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    else:  # state == 'absent'
        module.exit_json(
            msg="Volume {} doesn't exist on OVH public Cloud ".format(name),
            changed=False)


def main():
    run_module()


if __name__ == '__main__':
    main()
