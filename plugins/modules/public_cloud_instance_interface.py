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
    interface_openstack_id:
        required: true
        description:
            - The network's openstack id to attache the interface to
            - This is returned by a call to public_cloud_private_network_info.
'''

EXAMPLES = r'''
  - name: Create vrack interface
  synthesio.ovh.public_cloud_instance_interface:
    service_name: "{{ service_name }}"
    instance_id: "{{ instance_id }}"
    interface_ip: "{{ network_vrack.ip }}"
    interface_openstack_id: "{{ network_info.openstack_id }}"
  delegate_to: localhost
  register: interface_metadata

'''

RETURN = r''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True),
        instance_id=dict(required=True),
        state=dict(choices=['present', 'absent'], default='present'),
        interface_ip=dict(required=True),
        interface_openstack_id=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    service_name = module.params['service_name']
    instance_id = module.params['instance_id']
    state = module.params['state']
    interface_ip = module.params['interface_ip']
    interface_openstack_id = module.params['interface_openstack_id']

    if module.check_mode:
        module.exit_json(msg="Ensure interface {} on {} is {} on instance id {} - (dry run mode)"
                         .format(interface_ip, interface_openstack_id, state, instance_id),
                         changed=True)

    if state == 'absent':
        # Need to get the interface id (via /cloud/project/{serviceName}/instance/{instanceId}/interface).
        # How to manage multiple interfaces ?
        module.fail_json(msg="Removing an interface is not yet implemented")
    if state == 'present':
        result = client.wrap_call("POST", f"/cloud/project/{service_name}/instance/{instance_id}/interface",
                                  ip=interface_ip,
                                  networkId=interface_openstack_id)
        module.exit_json(
            changed=True,
            msg="Interface has been attached to instance id {}".format(
                instance_id),
            **result)


def main():
    run_module()


if __name__ == '__main__':
    main()
