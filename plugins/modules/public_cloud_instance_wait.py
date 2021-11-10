#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_instance_wait
short_description: Wait for an Public Cloud Instance to become active
description:
    - Wait until the public cloud instance installation is done (status == active)
    - Can be used to wait before running next task in your playbook
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The OVH API service_name is  Public cloud project Id
    instance_id:
        required: true
        description: The instance uuid
    target_status:
        required: true
        description: target status to wait for
        default: ACTIVE
    max_retry:
        required: false
        description: Number of retries
        default: 30
    sleep:
        required: false
        description: Time to sleep between retries
        default: 20

'''

EXAMPLES = '''
synthesio.ovh.public_cloud_instance_wait:
  instance_id: "{{ instance_id }}"
  service_name: "{{ service_name }}"
delegate_to: localhost
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import ovh_api_connect, ovh_argument_spec
from ansible.utils.display import Display
from ansible import constants
import time

display = Display()

try:
    from ovh.exceptions import APIError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True),
        instance_id=dict(required=True),
        max_retry=dict(required=False, default=30),
        sleep=dict(required=False, default=20),
        target_status=dict(required=False, default='ACTIVE')
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    instance_id = module.params['instance_id']
    service_name = module.params['service_name']
    max_retry = module.params['max_retry']
    sleep = module.params['sleep']
    target_status = module.params['target_status']

    is_target_status = False
    
    if module.check_mode:
        module.exit_json(msg="done - (dry run mode)", changed=False)

    for i in range(1, int(max_retry)):

        display.display("%i out of %i" %
                        (i, int(max_retry)), constants.COLOR_VERBOSE)
        result = None
        try:
            result = client.get('/cloud/project/%s/instance/%s' % (service_name, instance_id))

            if result and 'status' in result:
                is_target_status = (result['status'] == target_status)

        except APIError as api_error:
            return module.fail_jsonl(msg="Failed to call OVH API: {0}".format(api_error))
        
        if is_target_status:
            module.exit_json(changed=True, **result)

        time.sleep(float(sleep))

    module.fail_json(msg="Max wait time reached, about %i x %i seconds" % (i, int(sleep)))


def main():
    run_module()


if __name__ == '__main__':
    main()
