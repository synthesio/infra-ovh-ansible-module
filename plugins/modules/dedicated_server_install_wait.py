#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
---
module: dedicated_server_install_wait
short_description: Wait until the dedicated server installation is done
description:
    - Wait until the dedicated server installation is done
    - Can be used to wait before running next task in your playbook
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: Ovh name of the server
    max_retry:
        required: false
        description: Number of retry
        default: 240
    sleep:
        required: false
        description: Time to sleep between retries
        default: 10

'''

EXAMPLES = '''
- name: Wait until the dedicated server installation is done
  synthesio.ovh.dedicated_server_install_wait:
    service_name: "ns12345.ip-1-2-3.eu"
    max_retry: "240"
    sleep: "10"
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
        max_retry=dict(required=False, default=240),
        sleep=dict(required=False, default=10)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    service_name = module.params['service_name']
    max_retry = module.params['max_retry']
    sleep = module.params['sleep']

    if module.check_mode:
        module.exit_json(msg="done - (dry run mode)", changed=False)

    for i in range(1, int(max_retry)):
        # Messages cannot be displayed in real time (yet)
        # https://github.com/ansible/proposals/issues/92
        display.display("%i out of %i" %
                        (i, int(max_retry)), constants.COLOR_VERBOSE)
        try:
            tasklist = client.get(
                '/dedicated/server/%s/task' % service_name,
                function='reinstallServer')
            result = client.get(
                '/dedicated/server/%s/task/%s' % (service_name, max(tasklist)))
        except APIError as api_error:
            return module.fail_jsonl(msg="Failed to call OVH API: {0}".format(api_error))

        message = ""
        # Get more details in installation progression
        if "done" in result['status']:
            module.exit_json(msg="{}: {}".format(result['status'], message), changed=False)

        progress_status = client.get(
            '/dedicated/server/%s/install/status' % service_name
        )
        if 'message' in progress_status and progress_status['message'] == 'Server is not being installed or reinstalled at the moment':
            message = progress_status['message']
        else:
            for progress in progress_status['progress']:
                if progress["status"] == "doing":
                    message = progress['comment']
        display.display("{}: {}".format(result['status'], message), constants.COLOR_VERBOSE)
        time.sleep(float(sleep))
    module.fail_json(msg="Max wait time reached, about %i x %i seconds" % (i, int(sleep)))


def main():
    run_module()


if __name__ == '__main__':
    main()
