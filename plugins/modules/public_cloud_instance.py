#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_instance
short_description: Manage OVH API for public cloud instance creatikon
description:
    - This module manage the creation of an instance on OVH public Cloud
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    name:
        required: false
        description: The instance name to create
    sshKeyId:
        required: false
        description: The sshKey Id to add
    flavor_id:
        required: false
        description: The id of the commercial name
    image_id:
        required: false
        description: The id of the image/os to deploy on the instance
    region:
        required: false
        description: The region where to deploy the instance
    networks:
        required: false
        description: The network configuration.
          Can be the full array of the network configuration
    instance_id:
        required: false
        description: the instance uuid

'''

EXAMPLES = '''
- name: run installation
  synthesio.ovh.ovh_public_cloud_instance:
    name: "{{ inventory_hostname }}"
    sshKeyId: "{{ sshKeyId }}"
    service_name: "{{ service_name }}"
    networks: "{{ networks }}"
    flavor_id: "{{ flavor_id }}"
    region: "{{ region }}"
    image_id: "{{ image_id }}"
  delegate_to: localhost
  register: instance_metadata
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
        name=dict(required=True),
        flavor_id=dict(required=True),
        image_id=dict(required=False, default=None),
        service_name=dict(required=True),
        sshKeyId=dict(required=False, default=None),
        region=dict(required=True),
        networks=dict(required=False, default=[], type="list"),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    name = module.params['name']
    service_name = module.params['service_name']
    flavor_id = module.params['flavor_id']
    image_id = module.params['image_id']
    service_name = module.params['service_name']
    ssh_key_id = module.params['ssh_key_id']
    region = module.params['region']
    networks = module.params['networks']

    try:
        result = client.post('/cloud/project/%s/instance' % service_name,
                             flavorId=flavor_id,
                             imageId=image_id,
                             monthlyBilling=False,
                             name=name,
                             region=region,
                             networks=networks,
                             sshKeyId=ssh_key_id
                             )

        module.exit_json(changed=True, **result)
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
