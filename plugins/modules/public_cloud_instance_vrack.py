#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type


DOCUMENTATION = '''
---
module: public_cloud_instance_vrack
short_description: Manage OVH API for public cloud attach Vrack
description:
    - This module manage the attach of an Vrack on OVH instance public Cloud
author: Article714 (M. Piriou, C. Guychard)
requirements:
    - ovh >= 0.5.0
options:
    instance_id:
        required: true
        description:
            - The instance name
    service_name:
        required: true
        description:
            - The id of the project
    vrack:
        required: true
        description:
            - The id of the Vrack
    state:
        required: false
        default: present
        choices: ['present','absent']
        description: Indicate the desired state of vrack
'''

EXAMPLES = '''
- name: "Attach a Vrack to instance {{ instance_id }} on public cloud OVH"
  synthesio.ovh.public_cloud_instance_vrack:
    instance_id: "{{ instance_id }}"
    service_name: "{{ service_name }}"
    vrack: "{{ vrack }}"
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
        vrack=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    service_name = module.params['service_name']
    vrack = module.params['vrack']
    instance_id= module.params['instance_id']
    state = module.params['state']

    if module.check_mode:
        module.exit_json(
            msg="{} succesfully {} on {} / {} - (dry run mode)".format(
                service_name, instance_id , state, vrack),
            changed=True)


    is_already_registered = False   
    vrack_if=None
    # list existing interfaces
    try:
        interfaces_list = client.get(
                '/cloud/project/{0}/instance/{1}/interface'.format(service_name, instance_id))
        
        for netif in interfaces_list:
            if netif['networkId'] == vrack:
                is_already_registered=True
                vrack_if = netif

    except APIError as api_error:
        module.fail_json(msg="Failed to get interfaces list: {0}".format(api_error))
        
    # Attach or detach
    
    if state == 'present' and not is_already_registered:
        try:
            attach_result = client.post(
                '/cloud/project/{0}/instance/{1}/interface'.format(service_name, instance_id), networkId=vrack)
            module.exit_json(changed=True, **attach_result)

            module.exit_json( msg="vrack {} interface has been added to instance {}".format(
                                 vrack, instance_id), result= attach_result, changed=True)

        except APIError as api_error:
            module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    if state == 'absent' and is_already_registered:
        if vrack_if:
            try:
                detach_result = client.delete(
                    '/cloud/project/{0}/instance/{1}/interface/{2}'.format(service_name, instance_id, vrack_if['id']))

                module.exit_json( msg="vrack {} interface has been deleted from instance {}".format(
                                 vrack, instance_id), result= detach_result,  changed=True)

            except APIError as api_error:
                module.fail_json(msg="Failed to remove Vrack interface: {0}".format(api_error))



    module.exit_json( msg="vrack {} interface already exists on instance {}".format(
                                 vrack, instance_id), changed=False)    
                                 
def main():
    run_module()


if __name__ == '__main__':
    main()
