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

EXAMPLES = r'''
- name: Wait until the dedicated server installation is done
  synthesio.ovh.dedicated_server_install_wait:
    service_name: "ns12345.ip-1-2-3.eu"
    max_retry: "240"
    sleep: "10"
  delegate_to: localhost
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, OVHResourceNotFound, ovh_argument_spec
import time


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
    client = OVH(module)

    service_name = module.params['service_name']
    max_retry = module.params['max_retry']
    sleep = module.params['sleep']

    if module.check_mode:
        module.exit_json(msg="done - (dry run mode)", changed=False)

    for i in range(1, int(max_retry)):
        tasklist = client.wrap_call(
            "GET",
            f"/dedicated/server/{service_name}/task",
            function='reinstallServer')
        result = client.wrap_call(
            "GET",
            f"/dedicated/server/{service_name}/task/{max(tasklist)}")

        message = ""
        # Get more details in installation progression
        if "done" in result['status']:
            module.exit_json(msg="{}: {}".format(result['status'], message), changed=False)

        try:
            progress_status = client.wrap_call(
                "GET",
                f"/dedicated/server/{service_name}/install/status"
            )
        except OVHResourceNotFound:
            module.debug('Got 404ed while trying to get the progress status, installation might be done')
            continue

        for progress in progress_status['progress']:
            if progress["status"] == "doing":
                module.debug(msg='Current progress: {}'.format(progress['comment']))

        time.sleep(float(sleep))
    module.fail_json(msg="Max wait time reached, about %i x %i seconds" % (i, int(sleep)))


def main():
    run_module()


if __name__ == '__main__':
    main()
