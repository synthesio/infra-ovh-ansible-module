#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule


DOCUMENTATION = '''
---
module: dedicated_server_terminate
short_description: Terminate a dedicated server renting
description:
    - Terminate a dedicated server renting. Need mail confirmation
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service_name to terminate
'''

EXAMPLES = '''
synthesio.ovh.dedicated_server_terminate:
  service_name: "{{ service_name }}"
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
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    service_name = module.params['service_name']

    if module.check_mode:
        module.exit_json(changed=True, msg="Terminate {} is done, please confirm via the email sent - (dry run mode)".format(service_name))

    try:
        client.post(
            '/dedicated/server/%s/terminate' % service_name
        )

        module.exit_json(changed=False, msg="Terminate {} is done, please confirm via the email sent".format(service_name))

    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
