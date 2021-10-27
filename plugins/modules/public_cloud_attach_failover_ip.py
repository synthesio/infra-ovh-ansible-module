#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type


DOCUMENTATION = '''
---
module: attach_failover_ip
short_description: Manage OVH API for public cloud attach IP fail-over
description:
    - This module manage the attach of an IP fail-over on OVH public Cloud
author: Article714
requirements:
    - ovh >= 0.5.0
options:
    name:
        required: true
        description:
            - The instance name
    region:
        required: true
        description:
            - The region where to deploy the instance
    service_name:
        required: true
        description:
            - The id of the project
    id:
        required: true
        description:
            - The id of the IP fail-over
'''

EXAMPLES = '''
- name: "Attach an fail-over IP to {{ name }} on public cloud OVH"
  synthesio.ovh.public_cloud_attach_failover_ip:
    name: "{{ name }}"
    service_name: "{{ service_name }}"
    id: "{{ id }}"
    region: "{{ region }}"
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
        name=dict(required=True),
        service_name=dict(required=True),
        id=dict(required=True),
        region=dict(required=True),
        instanceId=dict(required=False),
        attach_ip=dict(required=False, default=True, type="bool")
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    name = module.params['name']
    service_name = module.params['service_name']
    id = module.params['id']
    region = module.params['region']
    instanceId= module.params['instanceId']
    attach_ip = module.params['attach_ip']

    try:
        instances_list = client.get('/cloud/project/{0}/instance'.format(service_name,
                            region=region))
    except APIError as api_error:
        module.fail_json(msg="Erreur 1: {0}".format(api_error))

    for i in instances_list:

        if i['name'] == name:
          instanceId = i['id']

        if attach_ip:
                try:
                    attach_result = client.post(
                        '/cloud/project/{0}/ip/failover/{1}/attach'.format(service_name, id), instanceId=instanceId)
                    module.exit_json(changed=True, **attach_result)

                except APIError as api_error:
                   module.fail_json(msg="Impossible d'appeler l'API OVH: {0}".format(api_error))

def main():
    run_module()


if __name__ == '__main__':
    main()
