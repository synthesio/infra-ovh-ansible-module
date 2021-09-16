#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
---
module: dedicated_server_boot
short_description: Change the bootid of a dedicated server.
description:
    - change the bootid and can reboot a dedicated server.
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description:
        - The server to manage
    boot:
        required: true
        default: harddisk
        choices: ['harddisk','rescue']
        description:
            - Which way you want to boot your dedicated server
    force_reboot:
        required: false
        default: false
        choices: ['true','false']
        description:
            - When you want to force a dedicated server reboot

'''

EXAMPLES = '''
- name: Change the bootid of a dedicated server to rescue
  synthesio.ovh.dedicated_server_boot:
    service_name: {{ service_name }}
    boot: "rescue"
    force_reboot: "true"
  delegate_to: localhost
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
        boot=dict(required=True, choices=['harddisk', 'rescue']),
        force_reboot=dict(required=False, default=False, type='bool')
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    service_name = module.params['service_name']
    boot = module.params['boot']
    force_reboot = module.params['force_reboot']
    changed = False

    bootid = {'harddisk': 1, 'rescue': 1122}
    if module.check_mode:
        module.exit_json(
            msg="{} is now set to boot on {}. Reboot in progress... - (dry run mode)".format(service_name, boot),
            changed=False)

    try:
        check = client.get(
            '/dedicated/server/%s' % service_name
        )
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    if bootid[boot] != check['bootId']:
        try:
            client.put(
                '/dedicated/server/%s' % service_name,
                bootId=bootid[boot]
            )
            changed = True
        except APIError as api_error:
            module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    if force_reboot:
        try:
            client.post(
                '/dedicated/server/%s/reboot' % service_name
            )
        except APIError as api_error:
            module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

        module.exit_json(msg="{} is now forced to reboot on {}".format(service_name, boot), changed=True)

    module.exit_json(msg="{} is now set to boot on {}".format(service_name, boot), changed=changed)


def main():
    run_module()


if __name__ == '__main__':
    main()
