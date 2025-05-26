#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
module: dedicated_server_task_status
short_description: Check the status of an OVH server task
description:
    - Query OVH API to check the status of a dedicated server task (reinstall, etc.)
options:
    service_name:
        required: true
        type: str
        description: The OVH service name of the server (e.g. nsXXXX.ip-...)
    task_id:
        required: true
        type: int
        description: The task ID returned by a previous action (e.g. reinstall)
'''

EXAMPLES = '''
- name: Check OVH task status
  dedicated_server_task_status:
    service_name: "xxxx.ip-xx-xx-xx.eu"
    task_id: xxxxxx
  register: task_status

- debug:
    msg: "Task status is {{ task_status.status }}"
'''

RETURN = '''
status:
  description: Status of the task (e.g., "done", "running", "error")
  type: str
  returned: always
result:
  description: Full API response from OVH
  type: dict
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec

def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True, type='str'),
        task_id=dict(required=True, type='int'),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    client = OVH(module)

    service_name = module.params['service_name']
    task_id = module.params['task_id']

    try:
        result = client.wrap_call(
            "GET",
            f"/dedicated/server/{service_name}/task/{task_id}"
        )
    except Exception as e:
        module.fail_json(msg=f"Failed to fetch task status: {str(e)}")

    module.exit_json(
        changed=False,
        status=result.get("status"),
        result=result
    )


def main():
    run_module()


if __name__ == '__main__':
    main()
