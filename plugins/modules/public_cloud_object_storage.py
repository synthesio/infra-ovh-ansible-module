#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = r'''
---
module: public_cloud_object_storage

short_description: Manage OVH API for public cloud S3 bucket.

description:
    - This module manage S3 bucket creation/deletion on OVH public cloud (not the legacy swift).

requirements:
    - ovh >= 0.5.0

options:
    service_name:
        required: true
        description: The service_name (OVH public cloud project ID)
    region:
        required: true
        description: The region where to create the S3 bucket
    name:
        required: true
        description: The S3 bucket name
    state:
        required: false
        default: present
        choices: ['present', 'absent']
        description: Indicate the desired state of the S3 bucket
    force:
        required: false
        default: false
        choices: ['true', 'false']
        description: When state is absent, force deletion of the S3 bucket even if not empty (up to 1000 objects deletion)
'''

EXAMPLES = r'''
- name: Ensure S3 bucket is in desired state
  synthesio.ovh.public_cloud_object_storage:
    service_name: "{{ service_name }}"
    region: "{{ region }}"
    name: "bucket-{{ inventory_hostname }}"
  delegate_to: localhost
  register: object_storage_metadata
'''

RETURN = r''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    """Create or delete an OVH public cloud S3 bucket"""
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True),
        region=dict(required=True),
        name=dict(required=True),
        state=dict(choices=['present', 'absent'], default='present'),
        force=dict(required=False, default=False, type='bool')
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    service_name = module.params['service_name']
    region = module.params['region']
    name = module.params['name']
    state = module.params['state']
    force = module.params['force']

    if module.check_mode:
        module.exit_json(msg="Ensure S3 bucket {} is {} - (dry run mode)".format(name, state),
                         changed=True)

    bucket_list = []
    bucket_list = client.wrap_call("GET", f"/cloud/project/{service_name}/region/{region}/storage")

    # Search if the bucket exists based on its name amongst all buckets in project
    for bucket in bucket_list:
        if bucket['name'] == name:
            bucket_details = client.wrap_call("GET",
                                              f"/cloud/project/{service_name}/region/{region}/storage/{name}",
                                              limit=1000)
            if state == 'absent':
                # Bucket needs to be empty to delete it through OVH API
                if (bucket_details['objectsCount'] != 0):
                    if not force:
                        module.fail_json(msg="Bucket {} ({}) is not empty. Use option 'force: true' to force its deletion".format(name, region),
                                         changed=False,
                                         **bucket_details)
                    else:  # force == 'true', cleaning bucket up to 1000 objects (max value for OVH API)
                        for bucket_object in bucket_details['objects']:
                            _ = client.wrap_call("DELETE",
                                                 f"/cloud/project/{service_name}/region/{region}/storage/{name}/object/{bucket_object['key']}")
                _ = client.wrap_call("DELETE",
                                     f"/cloud/project/{service_name}/region/{region}/storage/{name}")

                module.exit_json(msg="Bucket {} ({}) was deleted from OVH public cloud".format(name, region),
                                 changed=True)

            else:  # state == 'present':
                module.exit_json(msg="Bucket {} ({}) already exists on OVH public cloud".format(name, region),
                                 changed=False,
                                 **bucket_details)

    # Bucket does not yet exist on this project
    if state == 'present':
        result = client.wrap_call("POST",
                                  f"/cloud/project/{service_name}/region/{region}/storage",
                                  name=name)
        module.exit_json(msg="Bucket {} ({}) was created on OVH public cloud".format(name, result['virtualHost']),
                         changed=True,
                         **result)

    else:  # state == 'absent'
        module.exit_json(msg="Bucket {} ({}) doesn't exist on OVH public cloud ".format(name, region),
                         changed=False)


def main():
    run_module()


if __name__ == '__main__':
    main()
