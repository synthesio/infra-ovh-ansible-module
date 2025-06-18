#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
---
module: dedicated_server_installation
short_description: Install a dedicated server using OVH API
description:
    - Install (or reinstall) an OVH dedicated server without template.
    - The documentation for parameters like customizations and storage can be found in the OVH API documentation.
    - https://eu.api.ovh.com/console/?section=%2Fdedicated%2Fserver&branch=v1#post-/dedicated/server/-serviceName-/reinstall
author: Synthesio SRE Team with an initial work from @jawadevops
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: OVH service name (e.g. nsXXXX.ip-XXX)
    operating_system:
        required: true
        description: OS template to use (e.g. debian12_64)
    customizations:
        required: false
        description: Customizations for installation
    storage:
        required: false
        description: Disk layout config (diskGroupId, RAID, etc.)
'''

EXAMPLES = r'''
- name: Reinstall OVH server
  dedicated_server_installation:
    service_name: "xxx.ip-xxx-xx-xx.eu"
    operating_system: "debian12_64"
    customizations:
      hostname: "ceph-2"
      sshKey: "{{ lookup('file', '~/.ssh/id_rsa.pub') }}"
      httpHeaders:
        Authorization: "Basic bG9naW46cGFzc3dvcmQ="
      imageURL: "https://github.com/ashmonger/akution_test/releases/latest/download/deb11k6.qcow2"
      language: fr-fr
    storage:
      - diskGroupId: 1
        partitioning:
          disks: 2
          layout:
            - fileSystem: ext4
              mountPoint: /
              raidLevel: 1
              size: 20480
            - fileSystem: xfs
              mountPoint: /srv
              raidLevel: 0
              size: 0
'''

RETURN = '''
task_id:
  description: Task ID of the installation operation
  returned: always
  type: int
'''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(type="str", required=True),
        operating_system=dict(type="str", required=True),
        customizations=dict(type="dict", required=False, default=None),
        storage=dict(type="list", required=False, default=None)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    client = OVH(module)

    service_name = module.params['service_name']
    os_template = module.params['operating_system']
    storage = module.params['storage']
    customizations = module.params['customizations']

    if module.check_mode:
        module.exit_json(msg=f"Installation in progress on {service_name} ({os_template}) - (dry run mode)",
                         changed=True)

    result = client.wrap_call(
        "POST",
        f"/dedicated/server/{service_name}/reinstall",
        operatingSystem=os_template,
        customizations=customizations,
        storage=storage
    )

    module.exit_json(
        changed=True,
        msg=f"Installation in progress on {service_name} ({os_template})",
        task_id=result.get("taskId")
    )


def main():
    run_module()


if __name__ == '__main__':
    main()
