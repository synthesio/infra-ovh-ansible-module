#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_instance
short_description: Manage OVH API for public cloud instance creation
description:
    - This module manage the creation of an instance on OVH public Cloud
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    name:
        required: true
        description:
            - The instance name to create
    ssh_key_id:
        required: false
        description:
            - The sshKey Id to add
    flavor_id:
        required: true
        description:
            - The id of the commercial name
    image_id:
        required: true
        description:
            - The id of the image/os to deploy on the instance
    region:
        required: true
        description:
            - The region where to deploy the instance
    networks:
        required: false
        description:
            - The network configuration.
            - Can be the full array of the network configuration
    service_name:
        required: true
        description:
            - The service_name
    monthly_billing:
        required: false
        default: false
        description:
            - Enable or not the monthly billing
    force_reinstall:
        required: false
        default: false
        choices: ['true','false']
        description:
            - When you want force reinstallation of instance already existing

'''

EXAMPLES = r'''
- name: "Launch install of {{ inventory_hostname }} on public cloud OVH"
  synthesio.ovh.public_cloud_instance:
    name: "{{ inventory_hostname }}"
    ssh_key_id: "{{ sshKeyId }}"
    service_name: "{{ service_name }}"
    networks: "{{ networks }}"
    flavor_id: "{{ flavor_id }}"
    region: "{{ region }}"
    image_id: "{{ image_id }}"
  delegate_to: localhost
  register: instance_metadata
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        name=dict(required=True),
        flavor_id=dict(required=True),
        image_id=dict(required=True),
        service_name=dict(required=True),
        ssh_key_id=dict(required=False, default=None),
        region=dict(required=True),
        networks=dict(required=False, default=[], type="list"),
        monthly_billing=dict(required=False, default=False, type="bool"),
        force_reinstall=dict(required=False, default=False, type="bool")
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    name = module.params['name']
    service_name = module.params['service_name']
    flavor_id = module.params['flavor_id']
    image_id = module.params['image_id']
    ssh_key_id = module.params['ssh_key_id']
    region = module.params['region']
    networks = module.params['networks']
    monthly_billing = module.params['monthly_billing']
    force_reinstall = module.params['force_reinstall']

    instances_list = client.wrap_call("GET",
                                      f"/cloud/project/{service_name}/instance",
                                      region=region)

    for i in instances_list:

        if i['name'] == name:
            instance_id = i['id']
            instance_details = client.wrap_call("GET", f"/cloud/project/{service_name}/instance/{instance_id}")

            if force_reinstall:
                reinstall_result = client.wrap_call(
                    "POST",
                    f"/cloud/project/{service_name}/instance/{instance_id}/reinstall",
                    imageId=image_id)
                module.exit_json(changed=True, **reinstall_result)

            module.exit_json(changed=False,
                             msg="Instance {} [{}] in region {} is already installed".format(name, instance_id, region),
                             **instance_details)

    result = client.wrap_call("POST",
                              f"/cloud/project/{service_name}/instance",
                              flavorId=flavor_id,
                              imageId=image_id,
                              monthlyBilling=monthly_billing,
                              name=name,
                              region=region,
                              networks=networks,
                              sshKeyId=ssh_key_id
                              )

    module.exit_json(changed=True, **result)


def main():
    run_module()


if __name__ == '__main__':
    main()
