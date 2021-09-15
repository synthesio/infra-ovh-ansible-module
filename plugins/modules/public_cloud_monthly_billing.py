#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_monthly_billing
short_description: Enable monthly billing on an instance
description:
    - This module enable monthly billing on an instance. This CAN'T be disabled.
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    instance_id:
        required: true
        description: the instance uuid
    service_name:
        required: true
        description: The service_name

'''

EXAMPLES = '''
- name: Enable monthly billing
  synthesio.ovh.public_cloud_monthly_billing:
    service_name: "{{ service_name }}"
    instance_id: "{{ instance_id }}"
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
        instance_id=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    client = ovh_api_connect(module)

    service_name = module.params['service_name']
    instance_id = module.params['instance_id']

    if module.check_mode:
        module.exit_json(msg="Monthly Billing enabled on {} ! - (dry run mode)".format(instance_id), changed=True)

    try:
        result = client.get('/cloud/project/%s/instance/%s' % (service_name, instance_id))
        if result['monthlyBilling'] is not None and result['monthlyBilling']['status'] == "ok":
            module.exit_json(changed=False, msg="Monthly billing already enabled")

        result = client.post('/cloud/project/%s/instance/%s/activeMonthlyBilling' % (service_name, instance_id))
        module.exit_json(changed=True, **result)
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
