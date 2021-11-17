#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type


DOCUMENTATION = '''
---
module: public_cloud_instance_private_network
short_description: Manage OVH API for public cloud attach private_network
description:
    - This module manage the attach of an private_network on OVH instance public Cloud
author: Article714 (M. Piriou, C. Guychard)
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description:
            - The OVH API service_name is  Public cloud project Id, that can be obtained using public_cloud_project_info module
    instance_id:
        required: true
        description:
            - The instance id
    private_network_id:
        required: true
        description:
            - The id of the private_network
    static_ip:
        required: false
        description:
            - The static IP to set on new interface
    state:
        required: false
        default: present
        choices: ['present','absent']
        description: Indicate the desired state of private_network
'''

EXAMPLES = '''
- name: "Attach a private_network to instance {{ instance_id }} on public cloud OVH"
  synthesio.ovh.public_cloud_instance_private_network:
    instance_id: "{{ instance_id }}"
    service_name: "{{ service_name }}"
    private_network_id: "{{ private_network_id }}"
    static_ip: "{{ static_ip }}"
    state: present
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
        state=dict(choices=['present', 'absent'], default='present'),
        instance_id=dict(required=True),
        private_network_id=dict(required=True),
        static_ip=dict(required=False,default=None)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    service_name = module.params['service_name']
    private_network_id = module.params['private_network_id']
    static_ip = module.params['static_ip']
    instance_id= module.params['instance_id']
    state = module.params['state']

    if module.check_mode:
        module.exit_json(
            msg="{}/{} successfully configured ({}) on  private_network {} - (dry run mode)".format(
                instance_id,service_name , state, private_network_id ),
            changed=True)


    is_already_registered = False
    private_network_if=None

    # list existing interfaces
    try:
        interfaces_list = client.get(
                '/cloud/project/{0}/instance/{1}/interface'.format(service_name, instance_id))

        for netif in interfaces_list:
            if netif['networkId'] == private_network_id:
                is_already_registered=True
                private_network_if = netif

    except APIError as api_error:
        module.fail_json(msg="Failed to get interfaces list: {0}".format(api_error))

    # Attach or detach
    if state == 'present':
        if not is_already_registered:
            try:
                if static_ip:
                    attach_result = client.post(
                        '/cloud/project/{0}/instance/{1}/interface'.format(service_name, instance_id), networkId=private_network_id, ip=static_ip)
                    module.exit_json(changed=True, **attach_result)
                else:
                    attach_result = client.post(
                        '/cloud/project/{0}/instance/{1}/interface'.format(service_name, instance_id), networkId=private_network_id)
                    module.exit_json(changed=True, **attach_result)

                module.exit_json( msg="private_network {} interface has been added to instance {}".format(
                                    private_network_id, instance_id), result= attach_result, changed=True)

            except APIError as api_error:
                module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

        module.exit_json( msg="private_network {} interface already exists on instance {}".format(
                                    private_network_id, instance_id), changed=False)

    else:
        if is_already_registered:
            try:
                detach_result = client.delete(
                    '/cloud/project/{0}/instance/{1}/interface/{2}'.format(service_name, instance_id, private_network_if['id']))

                module.exit_json( msg="private_network {} interface has been deleted from instance {}".format(
                                    private_network_id, instance_id), result= detach_result,  changed=True)

            except APIError as api_error:
                module.fail_json(msg="Failed to remove private_network interface: {0}".format(api_error))

        module.exit_json( msg="private_network {} interface does not exist on instance {}".format(
                                    private_network_id, instance_id), changed=False)


    module.fail_json( msg="do not know how to deal with private_network information", changed=False)


def main():
    run_module()


if __name__ == '__main__':
    main()
