#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_imageid_info
short_description: Get image id based on human name in ovh repository or in own snapshot repository
description:
    - Get imageid based on human name ("Debian 10", "Ubuntu 21.04","Centos 8", etc)
    - The imageid change between region
    - The retrieved imageid can be used to spawn a new instance
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    name:
        required: true
        description: The human name of the image ("Debian 10", "Ubuntu 21.04","Centos 8", etc)
    region:
        required: true
        description: The region where to lookup for imageid
    service_name:
        required: true
        description: The service_name

'''

EXAMPLES = r'''
- name: Get image id
  synthesio.ovh.public_cloud_imageid_info:
    service_name: "{{ service_name }}"
    region: "GRA7"
    name: "Debian 10"
  delegate_to: localhost
  register: image_id
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True),
        name=dict(required=True),
        region=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    service_name = module.params['service_name']
    name = module.params['name']
    region = module.params['region']

    # Get images list
    result_image = client.wrap_call("GET", f"/cloud/project/{service_name}/image",
                                    region=region)

    # Get snapshot list
    result_snapshot = client.wrap_call("GET", f"/cloud/project/{service_name}/snapshot",
                                       region=region)

    # search in both list
    for i in (result_image + result_snapshot):
        if i['name'] == name:
            image_id = i['id']
            module.exit_json(changed=False, id=image_id)

    module.fail_json(msg="Image {} not found in {}".format(name, region), changed=False)


def main():
    run_module()


if __name__ == '__main__':
    main()
