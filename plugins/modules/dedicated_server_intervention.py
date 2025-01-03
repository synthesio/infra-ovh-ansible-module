#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
---
module: dedicated_server_intervention
short_description: Enable or disable ovh intervention on a dedicated server
description:
    - Enable or disable ovh intervention on a dedicated server
author: tnosaj
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service name
    state:
        required: false
        description: Indicate the desired state of intervention
        choices:
          - enabled
          - disabled

'''

EXAMPLES = r'''
- name: "Enable proactive intervention on dedicated server {{ service_name }}"
  synthesio.ovh.dedicated_server_intervention:
    service_name: "{{ service_name }}"
    state: enabled
  delegate_to: localhost
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True),
        state=dict(choices=['enabled', 'disabled'], default='disabled')
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    service_name = module.params['service_name']
    state = module.params['state']

    if state == 'enabled':
        no_intervention_bool = False
    elif state == 'disabled':
        no_intervention_bool = True

    if module.check_mode:
        module.exit_json(msg="NoIntervention is now {} for {} - (dry run mode)".format(state, service_name), changed=True)

    server_state = client.wrap_call("GET", f"/dedicated/server/{service_name}")

    if server_state['noIntervention'] == no_intervention_bool:
        module.exit_json(msg="noIntervention is already {} on {}".format(state, service_name), changed=False)

    client.wrap_call("PUT", f"/dedicated/server/{service_name}", noIntervention=no_intervention_bool)

    module.exit_json(msg="noIntervention is now {} on {}".format(state, service_name), changed=True)


def main():
    run_module()


if __name__ == '__main__':
    main()
