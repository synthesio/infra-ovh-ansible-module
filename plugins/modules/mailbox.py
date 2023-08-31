#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
---
module: mailbox
short_description: Create/delete a mailbox or change password
description:
    - Manage a mailbox (create, delete, change password). Only mailbox service bundled with domain offer is supported at the moment (not MXPlan).
author: Filigran Engineering
requirements:
    - ovh >= 0.5.0
options:
    domain:
        required: true
        description:
            - The domain name
    account:
        required: true
        description:
            - Account name
    state:
        required: false
        default: present
        choices: ['present','absent']
        description: State of the mailbox
    password:
        required: false
        description:
            - Account's password - required for state=present
    description:
        required: false
        description: Description of the account
    size:
        required: false
        description: Account size - quota in bytes

'''

EXAMPLES = '''
synthesio.ovh.mailbox_create
  domain: mydomain.com
  account: john.doe
  password: changeme
  description: John Doe
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
        domain=dict(required=True),
        account=dict(required=True),
        state=dict(required=True, choices=['present', 'absent'], default='present'),
        password=dict(required=False),
        description=dict(required=False),
        size=dict(required=False)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    domain = module.params['domain']
    account = module.params['account']
    password = module.params['password']
    description = module.params['description']
    size = module.params['size']


    if module.check_mode:
        module.exit_json(
            msg="{}@{} succesfully created - (dry run mode)".format(
                account, domain),
            changed=True)

    try:
        result = client.post(
            '/email/domain/%s/account' % domain,
            domain=domain,
            accountName=account,
            password=password,
            description=description,
            size=size
        )
        module.exit_json(msg="{}@{} succesfully created".format(account, domain), result=result)
    except APIError as api_error:
        module.fail_json(
            msg="Failed to call OVH API: {0}".format(api_error))

def main():
    run_module()


if __name__ == '__main__':
    main()
