#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: dedicated_server_display_name
short_description: Modify the server display name in ovh manager
description:
    - Modify the server display name in ovh manager, to help you find your server with your own naming
author: Synthesio SRE Team
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

EXAMPLES = '''
- name: "Set display name to {{ display_name }} on server {{ ovhname }}"
  synthesio.ovh.dedicated_server_display_name:
    service_name: "{{ ovhname }}"
    display_name: "{{ display_name }}"
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
        display_name=dict(required=True),
        service_name=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    display_name = module.params['display_name']
    service_name = module.params['service_name']

    if module.check_mode:
        module.exit_json(msg="display_name has been set to {} ! - (dry run mode)".format(display_name), changed=True)

    try:
        result = client.get('/dedicated/server/%s/serviceInfos' % service_name)
    except APIError as api_error:
        return module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    service_id = result["serviceId"]
    resource = {
        "resource": {
            'displayName': display_name,
            'name': service_name}}
    try:
        client.put(
            '/service/%s' % service_id,
            **resource
        )
        module.exit_json(
            msg="displayName succesfully set to {} for {} !".format(display_name, service_name),
            changed=True)
    except APIError as api_error:
        return module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
