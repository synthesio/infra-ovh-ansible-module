#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
---
module: dedicated_server_install
short_description: Install a new dedicated server
description:
    - Install a new dedicated server
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: Ovh name of the server
    hostname:
        required: true
        description: Name of the new dedicated server
    template:
        required: true
        description: template to use to spawn the server
    ssh_key_name:
        required: false
        description: sshkey to deploy
    soft_raid_devices:
        required: false
        description: number of devices in the raid software

'''

EXAMPLES = r'''
- name: Install a new dedicated server
  synthesio.ovh.dedicated_server_install:
    service_name: "ns12345.ip-1-2-3.eu"
    hostname: "server01.example.net"
    template: "debian10_64"
    soft_raid_devices: "2"
    ssh_key_name: "mysshkeyname"
    partition_scheme_name: "custom"
  delegate_to: localhost
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True),
        hostname=dict(required=True),
        template=dict(required=True),
        ssh_key_name=dict(required=False, default=None),
        soft_raid_devices=dict(required=False, default=None),
        partition_scheme_name=dict(required=False, default="default")
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    service_name = module.params['service_name']
    hostname = module.params['hostname']
    template = module.params['template']
    ssh_key_name = module.params['ssh_key_name']
    soft_raid_devices = module.params['soft_raid_devices']
    partition_scheme_name = module.params['partition_scheme_name']

    if module.check_mode:
        module.exit_json(msg="Installation in progress on {} as {} with template {} - (dry run mode)".format(service_name, hostname, template),
                         changed=True)

    compatible_templates = client.wrap_call(
        "GET",
        f"/dedicated/server/{service_name}/install/compatibleTemplates"
    )
    if template not in compatible_templates["ovh"] and template not in compatible_templates["personal"]:
        module.fail_json(msg="{} doesn't exist in compatibles templates".format(template))

    details = {"details":
               {"language": "en",
                "customHostname": hostname,
                "sshKeyName": ssh_key_name,
                "softRaidDevices": soft_raid_devices}
               }

    client.wrap_call(
        "POST",
        f"/dedicated/server/{service_name}/install/start", **details, templateName=template, partitionSchemeName=partition_scheme_name)

    module.exit_json(msg="Installation in progress on {} as {} with template {}!".format(service_name, hostname, template), changed=True)


def main():
    run_module()


if __name__ == '__main__':
    main()
