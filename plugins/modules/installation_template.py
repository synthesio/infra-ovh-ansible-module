#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
---
module: installation_template
short_description: Manage installation templates for dedicated servers
description:
    - Manage installation templates for dedicated servers
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    template:
        required: true
        description: The template to create or delete
    state:
        required: false
        description: The state absent or present
    service_name:
        required: false
        description: The server name (used for hardware raid profils)
'''

EXAMPLES = '''
- name: Manage installation templates for dedicated servers
  synthesio.ovh.installation_template:
    template: "custom-debian-raid10-soft"
    state: "present"
  delegate_to: localhost
'''

RETURN = ''' # '''

import yaml
import os
import ast

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import ovh_api_connect, ovh_argument_spec

try:
    from ovh.exceptions import APIError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        template=dict(required=True),
        state=dict(choices=["present", "absent"], default="present"),
        service_name=dict(required=False, default=None)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    template = module.params['template']
    state = module.params['state']
    service_name = module.params['service_name']
    # The action plugin resolve the "template" variable path. So we need to re-extract the basename
    src_template = os.path.basename(template)

    if module.check_mode:
        module.exit_json(msg="template {} is now {} - dry run mode".format(template, state))

    try:
        template_list = client.get(
            '/me/installationTemplate'
        )
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    if state == 'absent':
        if src_template in template_list:
            try:
                client.delete('/me/installationTemplate/%s' % src_template)

                module.exit_json(msg="Template {} succesfully deleted".format(src_template), changed=True)
            except APIError as api_error:
                module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
        else:
            module.exit_json(msg="Template {} does not exists, do not delete it".format(src_template), changed=False)

    src = template
    with open(src, 'r') as stream:
        content = yaml.safe_load(stream)
    conf = {}
    for i, j in content.items():
        conf[i] = j

    # state == 'present'
    if src_template in template_list:
        module.exit_json(msg="Template {} already exists".format(src_template), changed=False)

    try:
        client.post(
            '/me/installationTemplate',
            baseTemplateName=conf['baseTemplateName'],
            defaultLanguage=conf['defaultLanguage'],
            name=conf['templateName']
        )
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    templates = {
        'customization': {
            "customHostname": conf['customHostname'],
            "postInstallationScriptLink": conf['postInstallationScriptLink'],
            "postInstallationScriptReturn": conf['postInstallationScriptReturn'],
            "sshKeyName": conf['sshKeyName'],
            "useDistributionKernel": conf['useDistributionKernel']},
        'defaultLanguage': conf['defaultLanguage'],
        'templateName': conf['templateName']}
    try:
        client.put(
            '/me/installationTemplate/{}'.format(conf['templateName']),
            **templates
        )
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    try:
        client.post(
            '/me/installationTemplate/{}/partitionScheme'.format(conf['templateName']),
            name=conf['partitionScheme'],
            priority=conf['partitionSchemePriority']
        )
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    if conf['isHardwareRaid']:
        try:
            result = client.get(
                '/dedicated/server/%s/install/hardwareRaidProfile' % service_name
            )
        except APIError as api_error:
            module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

        if len(result['controllers']) != 1:
            module.fail_json(
                msg="Failed to call OVH API: {0} Code can't handle more than one controller when using Hardware Raid setups")

        # XXX: Only works with a server who has one controller.
        # All the disks in this controller are taken to form one raid
        # In the future, some of our servers could have more than one controller
        # so we will have to adapt this code

        diskarray = result['controllers'][0]['disks'][0]['names']
        disks = []

        if conf['raidMode'] == 'raid1':
            # In raid1, we take the first two disks in the disk array
            disks = [diskarray[0], diskarray[1]]

        elif conf['raidMode'] == 'raid10' or conf['raidMode'] == 'raid60':
            # In raid10 or raid60, we configure two disk groups
            groups = [[], []]
            for i in range(len(diskarray)):
                if i < (len(diskarray) // 2):
                    groups[0].append(diskarray[i])
                else:
                    groups[1].append(diskarray[i])
            sep = ','
            disks = ['[' + (sep.join(groups[0])) + ']', '[' + (sep.join(groups[1])) + ']']

        else:
            # Fallback condition: pass every disk in the array (will be applied for raid0)
            disks = diskarray

        try:
            result = client.post(
                '/me/installationTemplate/%s/partitionScheme/%s/hardwareRaid' % (
                    conf['templateName'], conf['partitionScheme']),
                disks=disks,
                mode=conf['raidMode'],
                name=conf['partitionScheme'],
                step=1)
        except APIError as api_error:
            module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    partition = {}
    for k in conf['partition']:
        partition = ast.literal_eval(k)
        if 'volumeName' not in partition.keys():
            partition['volumeName'] = ""
        try:
            if 'raid' in partition.keys():
                client.post(
                    '/me/installationTemplate/%s/partitionScheme/%s/partition' % (
                        conf['templateName'], conf['partitionScheme']),
                    filesystem=partition['filesystem'],
                    mountpoint=partition['mountpoint'],
                    raid=partition['raid'],
                    size=partition['size'],
                    step=partition['step'],
                    type=partition['type'],
                    volumeName=partition['volumeName'])
            else:
                client.post(
                    '/me/installationTemplate/%s/partitionScheme/%s/partition' % (
                        conf['templateName'], conf['partitionScheme']),
                    filesystem=partition['filesystem'],
                    mountpoint=partition['mountpoint'],
                    size=partition['size'],
                    step=partition['step'],
                    type=partition['type'],
                    volumeName=partition['volumeName'])
        except APIError as api_error:
            module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
    try:
        client.post(
            '/me/installationTemplate/%s/checkIntegrity' % conf['templateName'])
        module.exit_json(
            msg="Template {} succesfully created".format(conf['templateName']),
            changed=True)
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
