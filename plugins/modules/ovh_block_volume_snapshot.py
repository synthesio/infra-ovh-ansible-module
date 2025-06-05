#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec

DOCUMENTATION = '''
---
module: ovh_block_volume_snapshot
short_description: Create a snapshot of an OVH Cloud block storage volume
description:
    - This module creates a snapshot for a given block storage volume on OVH Public Cloud.
options:
    service_name:
        description: The OVH Cloud project ID
        required: true
        type: str
    volume_id:
        description: The ID of the volume to snapshot
        required: true
        type: str
    snapshot_name:
        description: Name of the snapshot
        required: true
        type: str
    description:
        description: Description of the snapshot
        required: false
        type: str
author:
    - Your Name
'''

EXAMPLES = '''
- name: Create a snapshot of a volume
  ovh_block_volume_snapshot:
    service_name: "project-xyz"
    volume_id: "vol-abc123"
    snapshot_name: "daily-backup"
    description: "Snapshot taken automatically"
  delegate_to: localhost
'''

RETURN = '''
msg:
  description: Message about snapshot creation
  returned: always
  type: str
'''

def run_module():
    argument_spec = ovh_argument_spec()
    argument_spec.update(dict(
        service_name=dict(required=True, type='str'),
        volume_id=dict(required=True, type='str'),
        snapshot_name=dict(required=True, type='str'),
        description=dict(required=False, type='str', default="Snapshot created by Ansible")
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    client = OVH(module)

    service_name = module.params['service_name']
    volume_id = module.params['volume_id']
    snapshot_name = module.params['snapshot_name']
    description = module.params['description']

    try:
        result = client.wrap_call(
            "POST",
            f"/cloud/project/{service_name}/volume/{volume_id}/snapshot",
            name=snapshot_name,
            description=description
        )
        module.exit_json(changed=True, msg=f"Snapshot '{snapshot_name}' created successfully.", result=result)
    except Exception as e:
        module.fail_json(msg=f"Failed to create snapshot: {str(e)}")

def main():
    run_module()

if __name__ == '__main__':
    main()
