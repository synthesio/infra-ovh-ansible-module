#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: vps_display_name
short_description: Modify the vps display name in ovh manager
description:
    - Modify the vps display name in ovh manager, to help you find your vps with your own naming
author: Synthesio SRE Team / Paul Tap (armorica)
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service name
    display_name:
        required: true
        description: The display name to set

'''

EXAMPLES = r'''
- name: "Set display name to {{ display_name }} on vps {{ ovhname }}"
  synthesio.ovh.vps_display_name:
    service_name: "{{ ovhname }}"
    display_name: "{{ display_name }}"
  delegate_to: localhost
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        display_name=dict(required=True),
        service_name=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    display_name = module.params['display_name']
    service_name = module.params['service_name']

    if module.check_mode:
        module.exit_json(msg="display_name has been set to {} ! - (dry run mode)".format(display_name), changed=True)

    resource = {
        'displayName': display_name
        }

    # Retrieve the current values for displayName, keymap and netbootMode

    getResult=client.wrap_call(
        "GET",
        f"/vps/{service_name}",
        **resource
    )

    # Now check if the value is different and if necessary set it
    
    if getResult['displayName'] != display_name:
        putResult=client.wrap_call(
            "PUT",
            f"/vps/{service_name}",
            **resource
        )
        if putResult == None:
            module.exit_json(
                msg="displayName succesfully set to {} for {} !".format(display_name, service_name),
                changed=True)
        else:
            module.fail_json(
                msg="Error setting displayName for {} !".format(service_name)
                )
    else:
        module.exit_json(
            msg="No change required to displayName {} for {} !".format(display_name, service_name),
            changed=False)

def main():
    run_module()


if __name__ == '__main__':
    main()
