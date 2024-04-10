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

EXAMPLES = r'''
- name: Terminate a dedicated server renting
  synthesio.ovh.dedicated_server_terminate:
    service_name: "{{ service_name }}"
  delegate_to: localhost
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    service_name = module.params['service_name']

    if module.check_mode:
        module.exit_json(changed=True, msg="Terminate {} is done, please confirm via the email sent - (dry run mode)".format(service_name))

    client.wrap_call(
        "POST",
        f"/dedicated/server/{service_name}/terminate"
    )

    module.exit_json(changed=True, msg="Terminate {} is done, please confirm via the email sent".format(service_name))


def main():
    run_module()


if __name__ == '__main__':
    main()
