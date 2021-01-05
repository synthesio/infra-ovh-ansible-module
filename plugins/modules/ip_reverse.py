#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: ip_reverse
short_description: Modify reverse on IP
description:
    - Modify reverse on IP
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    ip:
        required: true
        description: The ip
    reverse:
        required: true
        description: The reverse to assign

'''

EXAMPLES = '''
synthesio.ovh.ip_reverse:
  ip: 192.0.2.1
  reverse: host.domain.example.
delegate_to: localhost
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import ovh_api_connect, ovh_argument_spec

try:
    from ovh.exceptions import APIError, ResourceNotFoundError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        ip=dict(required=True),
        reverse=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    ip = module.params['ip']
    reverse = module.params['reverse']

    if module.check_mode:
        module.exit_json(msg="Reverse {} to {} succesfully set ! - (dry run mode)".format(ip, reverse), changed=True)

    result = {}
    try:
        result = client.get('/ip/%s/reverse/%s' % (ip, ip))
    except ResourceNotFoundError:
        result['reverse'] = ''

    if result['reverse'] == reverse:
        module.exit_json(msg="Reverse {} to {} already set !".format(ip, reverse), changed=False)

    try:
        client.post(
            '/ip/%s/reverse' % ip,
            ipReverse=ip,
            reverse=reverse
        )
        module.exit_json(
            msg="Reverse {} to {} succesfully set !".format(ip, reverse),
            changed=True)
    except APIError as api_error:
        return module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
