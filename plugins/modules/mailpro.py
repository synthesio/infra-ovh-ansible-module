#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from datetime import datetime, timedelta

DOCUMENTATION = '''
---
module: mailpro
short_description: Create/delete a pro email or change password
description:
    - Manage a pro email (create, delete). Supports only OVH email pro service.
author: Filigran Engineering
requirements:
    - ovh >= 0.5.0
options:
    service:
        required: true
        description:
            - The service name
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
        description: State of the mailpro
    password:
        required: false
        description:
            - Account's password - required for state=present
    duration:
        required: false
        default: '12'
        choices: ['1', '12']
        description:
            - Duration of the email pro service in months (auto renewal)

'''

EXAMPLES = '''
synthesio.ovh.mailpro
  service: emailpro-ovh-1
  domain: mydomain.com
  account: john.doe
  password: changeme
  duration: 1
  payment_method_id: 123456
delegate_to: localhost
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec

try:
    from ovh.exceptions import APIError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service=dict(required=True),
        domain=dict(required=True),
        account=dict(required=True),
        state=dict(choices=['present', 'absent'], default='present'),
        password=dict(required=False),
        duration=dict(choices=['1', '12'], default='12'), # 1 month or 12 months
        payment_method_id=dict(required=False, type='int')
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    service = module.params['service']
    domain = module.params['domain']
    account = module.params['account']
    password = module.params['password']
    duration = module.params['duration']
    payment_method_id = module.params['payment_method_id']
    if duration == '12':
        renewperiod = 'yearly'
    else:
        renewperiod = 'monthly'


    if module.check_mode:
        module.exit_json(
            msg="{}@{} successfully created - (dry run mode)".format(
                account, domain),
            changed=True)

    try:

        accounts = client.wrap_call(
            "GET",
            '/email/pro/%s/account' % service,
        )
        if account in accounts:
            if module.params['state'] == 'present':
                if password:
                    # Update the password
                    client.wrap_call(
                        "POST",
                        '/email/pro/%s/account/%s@%s/changePassword' % (service, account, domain),
                        password=password
                    )
                    module.exit_json(msg="{}@{} already exists, password updated".format(account, domain), changed=True)
                else:
                    module.exit_json(msg="{}@{} already exists".format(account, domain), changed=False)
            else:
                # The email pro account will be reset to a @configureme.me config and will be available 
                result = client.wrap_call("DELETE", '/email/pro/%s/account/%s@%s' % (service, account, domain))
                module.exit_json(msg="{}@{} successfully deleted".format(account, domain), result=result, changed=True)
        else:
            if module.params['state'] == 'absent':
                module.exit_json(msg="{}@{} does not exist".format(account, domain), changed=False)
            else:
                    # Is there an email pro available
                    available_accounts = client.wrap_call(
                        "GET",
                        '/email/pro/%s/account?primaryEmailAddress=configureme' % service,
                    )
                    if not available_accounts:
                        if payment_method_id:
                            # Order a new email pro
                            orderid = client.wrap_call(
                                "POST",
                                '/order/email/pro/%s/account/%s?number=1' % (service, duration),
                                number=1
                            )['orderId']
                            # Pay the order
                            client.wrap_call(
                                "POST",
                                '/me/order/%s/pay' % (orderid),
                                paymentMethod={"id": payment_method_id}
                            )
                            # Get the ordered email pro
                            timeout = datetime.now() + timedelta(minutes=20)
                            while not available_accounts:
                                if datetime.now() > timeout:
                                    module.exit_json(msg="Timeout waiting for an email pro account to become available")
                                try:
                                    available_accounts = client.wrap_call(
                                        "GET",
                                        '/email/pro/%s/account?primaryEmailAddress=configureme' % service,
                                    )
                                    if not available_accounts:
                                        module.run_command(['sleep', '60'])
                                except APIError as e:
                                    module.exit_json(msg="Error while waiting for email pro account: %s" % str(e))
                        else:
                            module.exit_json(msg="Please provide a payment method id to order the email pro account", changed=False)
                    destination = available_accounts[0]

                    # Get the list of existing domain mailboxes (!=pro)
                    mailbox_accounts = client.wrap_call(
                        "GET",
                        '/email/domain/%s/account' % domain,
                    )
                    if account in mailbox_accounts:
                        if password:
                            # Migrate existing mailbox to email pro
                            result = client.wrap_call(
                                "POST",
                                '/email/domain/%s/account/%s/migrate/%s/destinationEmailAddress/%s/migrate' % (domain, account, service, destination),
                                password=password
                            )
                            module.exit_json(msg="{}@{} successfully migrated to email pro".format(account, domain), result=result, changed=True)
                        else:
                            module.exit_json(msg="{}@{} already exists as domain mailbox, please provide the password to migrate".format(account, domain))
                    else:
                        # Configure the email pro account
                        result = client.wrap_call(
                            "PUT",
                            '/email/pro/%s/account/%s' % (service, destination),
                            domain=domain,
                            login=account,
                            renewPeriod=renewperiod,
                            quota=10,
                            mailingfilter=['vaderetro']
                        )
                        if password:
                            # Set the password of the email pro account
                            client.wrap_call(
                                "POST",
                                '/email/pro/%s/account/%s@%s/changePassword' % (service, account, domain),
                                password=password
                            )
                        module.exit_json(msg="{}@{} successfully created as email pro".format(account, domain), result=result, changed=True)
                
    except APIError as api_error:
        module.fail_json(
            msg="Failed to call OVH API: {0}".format(api_error))

def main():
    run_module()


if __name__ == '__main__':
    main()
