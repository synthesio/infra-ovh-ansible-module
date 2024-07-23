#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = """
---
module: public_cloud_sshkey_id
short_description: Retrieve the id for a public cloud ssh public key
description:
    - This module retrieves the id for a OVH public cloud public key
author: Marco Sarti <m.sarti@onetag.com>
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description: The service name
    sshkey_name:
        required: true
        description: The sshkey name

"""

EXAMPLES = r"""
- name: Get the id of a OVH public cloud sshkey
  synthesio.ovh.public_cloud_sshkey_id:
    sshkey_name: "{{ sshkey_name }}"
    service_name: "{{ service_name }}"
  delegate_to: localhost
  register: sshkey_id
"""

RETURN = r"""
id:
    description: Id of a public cloud sshkey
    type: str
    sample:"62584e68636e5270"
"""

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import (
    OVH,
    ovh_argument_spec,
)


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(
        dict(
            service_name=dict(required=True),
            sshkey_name=dict(required=True),
        )
    )


    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    client = OVH(module)

    sshkey_name = module.params["sshkey_name"]
    service_name = module.params["service_name"]

    sshkey_id = False

    sshkeys_list = client.wrap_call(
        "GET", f"/cloud/project/{service_name}/sshkey"
    )

    for sshkey in sshkeys_list:
        if sshkey["name"] == sshkey_name:
            sshkey_id = sshkey["id"]

    # Exit if no key were found
    if not sshkey_id:
        module.fail_json(
            msg=f"No ssh key {sshkey_name} found", changed=False
        )

    module.exit_json(id=sshkey_id, changed=False)


def main():
    run_module()


if __name__ == "__main__":
    main()
