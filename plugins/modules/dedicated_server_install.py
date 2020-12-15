#!/usr/bin/python
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
    serviceName:
        required: true
        description: Ovh name of the server
    hostname:
        required: true
        description: Name of the new dedicated server
    template:
        required: true
        description: template to use to spawn the server

'''

EXAMPLES = '''
synthesio.ovh.dedicated_server_install:
    serviceName: "ns12345.ip-1-2-3.eu"
    hostname: "server01.example.net"
    template: "debian10_64"
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
        serviceName=dict(required=True),
        hostname=dict(required=True),
        template=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    serviceName = module.params['serviceName']
    hostname = module.params['hostname']
    template = module.params['template']

    if module.check_mode:
        module.exit_json(msg="Installation in progress on {} as {} with template {} - (dry run mode)".format(serviceName, hostname, template),
                         changed=True)

    try:
        compatible_templates = client.get(
            '/dedicated/server/%s/install/compatibleTemplates' % serviceName
        )
        if template not in compatible_templates["ovh"] and template not in compatible_templates["personal"]:
            module.fail_json(msg="{} doesn't exist in compatibles templates".format(template))
    except APIError as api_error:
        return module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    details = {"details":
               {"language": "en",
                "customHostname": hostname}
               }

    try:
        client.post(
            '/dedicated/server/%s/install/start' % serviceName, **details, templateName=template)

        module.exit_json(msg="Installation in progress on {} as {} with template {}!".format(serviceName, hostname, template), changed=True)

    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
