#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
module: dedicated_server_reinstall
short_description: Reinstall a dedicated server using OVH API
description:
    - Reinstall an OVH dedicated server using a specific OS, hostname, SSH key, and custom storage layout.
author:
    - "Inspired by Synthesio SRE team"
options:
    service_name:
        required: true
        type: str
        description: OVH service name (e.g. nsXXXX.ip-XXX)
    operating_system:
        required: true
        type: str
        description: OS template to use (e.g. debian12_64)
    hostname:
        required: true
        type: str
        description: Hostname to assign
    ssh_key:
        required: true
        type: str
        description: SSH public key string
    storage:
        required: true
        type: list
        description: Disk layout config (diskGroupId, RAID, etc.)
'''

EXAMPLES = r'''
- name: Reinstall OVH server
  dedicated_server_reinstall:
    service_name: "ns3255155.ip-217-182-89.eu"
    operating_system: "debian12_64"
    hostname: "ceph-2"
    ssh_key: "{{ lookup('file', '~/.ssh/id_rsa.pub') }}"
    storage:
      - diskGroupId: 1
        partitioning:
          disks: 2
          layout:
            - fileSystem: ext4
              mountPoint: /boot
              raidLevel: 1
              size: 2048
            - fileSystem: ext4
              mountPoint: /
              raidLevel: 1
              size: 0
'''

RETURN = '''
task_id:
  description: Task ID of the reinstall operation
  returned: always
  type: int
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec

def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(type="str", required=True),
        operating_system=dict(type="str", required=True),
        hostname=dict(type="str", required=True),
        ssh_key=dict(type="str", required=True),
        storage=dict(type="list", required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    client = OVH(module)

    service_name = module.params['service_name']
    os = module.params['operating_system']
    hostname = module.params['hostname']
    ssh_key = module.params['ssh_key']
    storage = module.params['storage']

    if module.check_mode:
        module.exit_json(changed=True, msg="[CHECK_MODE] Would reinstall server with provided config")

    try:
        result = client.wrap_call(
            "POST",
            f"/dedicated/server/{service_name}/reinstall",
            operatingSystem=os,
            customizations={
                "hostname": hostname,
                "sshKey": ssh_key
            },
            storage=storage
        )
    except Exception as e:
        module.fail_json(msg=f"Failed to trigger reinstall: {str(e)}")

    module.exit_json(
        changed=True,
        msg=f"Reinstall triggered for {service_name}",
        task_id=result.get("taskId")
    )

def main():
    run_module()

if __name__ == '__main__':
    main()
