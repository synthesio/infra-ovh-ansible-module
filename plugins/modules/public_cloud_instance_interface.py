#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = r'''
---
module: public_cloud_instance_interface

short_description: Manage OVH API for public cloud interfaces.

description:
    - This module attach or detach an interface of an instance on OVH public Cloud.

requirements:
    - ovh >= 0.5.0

options:
    service_name:
        required: true
        description: The service name
    instance_id:
        required: true
        description: The instance uuid
    state:
        required: false
        default: present
        choices: ['present','absent']
        description: Indicate the desired state of the interface
    interface_ip:
        required: true
        description: The fixed IP to set to the interface
    interface_network_id:
        required: true
        description: The network id to attache the interface to
'''

EXAMPLES = r'''
  - name: Create vrack interface
  synthesio.ovh.public_cloud_instance_interface:
    service_name: "{{ service_name }}"
    instance_id: "{{ instance_id }}"
    interface_ip: "{{ network_vrack.ip }}"
    interface_network_id: "{{ network_vrack.network_id }}"
  delegate_to: localhost
  register: interface_metadata

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
        instance_id=dict(required=True),
        state=dict(choices=['present', 'absent'], default='present'),
        interface_ip=dict(required=True),
        interface_network_id=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    service_name = module.params['service_name']
    instance_id = module.params['instance_id']
    state = module.params['state']
    interface_ip = module.params['interface_ip']
    interface_network_id = module.params['interface_network_id']

    if module.check_mode:
        module.exit_json(msg="Ensure interface {} on {} is {} on instance id {} - (dry run mode)"
                         .format(interface_ip, interface_network_id, state, instance_id),
                         changed=True)

    if state == 'absent':
        # Need to get the interface id (via /cloud/project/{serviceName}/instance/{instanceId}/interface).
        # How to manage multiple interfaces ?
        module.fail_json(msg="Removing an interface is not yet implemented")
    if state == 'present':
        try:
            result = client.post('/cloud/project/%s/instance/%s/interface' % (service_name, instance_id),
                                 ip=interface_ip,
                                 networkId=interface_network_id)
            module.exit_json(
                changed=True,
                msg="Interface has been attached to instance id {}".format(
                    instance_id),
                **result)

        except APIError as api_error:
            module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
