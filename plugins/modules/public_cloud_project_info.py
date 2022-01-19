#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type


DOCUMENTATION = '''
---
module: public_cloud_project_info
short_description: Get OVH Public cloud project information
description:
    - This module retrieves information from Public Cloud Project using human-readble project name (description)
author: Article714 (C. Guychard)
requirements:
    - ovh >= 0.5.0
options:
    project_name:
        required: true
        description:
            - The project human-readable name
'''

EXAMPLES = '''
- name: "Get info on OVH public cloud project {{ name }} "
  synthesio.ovh.public_cloud_project_info:
    project_name: "{{ name }}"
'''

RETURN = ''' All Project information '''


from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import ovh_api_connect, ovh_argument_spec

try:
    from ovh.exceptions import APIError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        project_name=dict(required=True),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    project_name = module.params['project_name']

    try:
        projects_list = client.get('/cloud/project')
    except APIError as api_error:
        module.fail_json(msg="Error getting projects list: {0}".format(api_error))

    for proj_id in projects_list:
        try:
            proj_info = client.get('/cloud/project/%s' % proj_id)
        except APIError as api_error:
            module.fail_json(msg="Error getting project info: {0}".format(api_error))

        if proj_info['description'] == project_name:
            break
        else:
            proj_info = None

    if proj_info:
        module.exit_json(changed=True, **proj_info)
    else:
        module.fail_json(msg="Public cloud project does not exist: %s" % project_name)


def main():
    run_module()


if __name__ == '__main__':
    main()
