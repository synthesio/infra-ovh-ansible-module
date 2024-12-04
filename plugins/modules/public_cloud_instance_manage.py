#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_instance_manage
short_description: Start or stop a OVH public cloud instance
description:
    - This module perform a Start/Stop/Shelve/Unshelve of an OVH public cloud instance
author: Saul Bertuccio <sbertuccio@gmail.com>
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service_name
    instance_id:
        required: true
        description: The instance uuid
    instance_action:
        required: true
        description: start, stop, shelve, unshelve
'''

EXAMPLES = r'''
- name: Stop a OVH public cloud instance
  synthesio.ovh.public_cloud_instance_manage:
    instance_id: "{{ instance_id }}"
    service_name: "{{ service_name }}"
    instance_action: stopped
  delegate_to: localhost
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec

def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True),
        instance_id=dict(required=True),
        instance_action=dict(required=True, choices=["start", "stop", "shelve", "unshelve"])
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    instance_id = module.params['instance_id']
    service_name = module.params['service_name']
    instance_action = module.params['instance_action']

    # Set the route depending on the action
    if instance_action  == "start":
      route = f"/cloud/project/{service_name}/instance/{instance_id}/start"
    elif instance_state == "stop":
      route = f"/cloud/project/{service_name}/instance/{instance_id}/stop"
    elif instance_state == "shelve":
      route = f"/cloud/project/{service_name}/instance/{instance_id}/shelve"
    elif instance_state == "unshelve":
      route = f"/cloud/project/{service_name}/instance/{instance_id}/unshelve"
    else:
      module.fail_json(msg=f"Instance action {instance_action} is unknown", changed=False)
     if module.check_mode:
        module.exit_json(msg=f"Action {instance_action} performed on {instance_id}. - (dry run mode)", changed=True)
    # Do the call
    client.wrap_call("POST", route)
 
    message = f"Action {instance_action} performed on {instance_id}. This might take a couple of minutes."
  
    module.exit_json(
      result=message,
      changed=True,
    )

def main():
    run_module()

if __name__ == '__main__':
    main()
