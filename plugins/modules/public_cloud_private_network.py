#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_private_network
short_description: Manage OVHcloud Public Cloud private networks
description:
  - Create or delete a private network in an OVHcloud Public Cloud project.
  - The network is identified by its C(name).
  - Immutable fields (C(vlan_id), C(regions)) cannot be changed after creation.
requirements:
  - python-ovh >= 0.5.0
options:
  service_name:
    description: Public cloud project ID.
    required: true
    type: str
  name:
    description: Network name. Used to identify the network idempotently.
    required: true
    type: str
  vlan_id:
    description:
      - VLAN ID, between 0 and 4095. Value 0 means no VLAN tagging.
      - Immutable after creation.
    required: false
    type: int
  regions:
    description:
      - List of regions where the network is activated (e.g. C(GRA11), C(SBG5)).
      - When omitted, the network is activated in all regions.
      - Immutable after creation.
    required: false
    type: list
    elements: str
  state:
    description: Desired state of the network.
    choices: ['present', 'absent']
    default: present
    type: str
author:
  - Jonathan Piron <jonathan@piron.at>
'''

EXAMPLES = r'''
- name: Create a private network
  synthesio.ovh.public_cloud_private_network:
    service_name: "{{ project_id }}"
    name: my-network
    vlan_id: 42
    regions:
      - GRA11
      - SBG5
    state: present

- name: Create a private network in all regions without VLAN tagging
  synthesio.ovh.public_cloud_private_network:
    service_name: "{{ project_id }}"
    name: my-network
    state: present

- name: Delete a private network
  synthesio.ovh.public_cloud_private_network:
    service_name: "{{ project_id }}"
    name: my-network
    state: absent
'''

RETURN = ''' # '''


def _find_network_by_name(client, service_name, name):
    """Return the network dict matching the given name, or None."""
    networks = client.wrap_call(
        "GET",
        f"/cloud/project/{service_name}/network/private",
    )
    for network in networks:
        if network.get("name") == name:
            return network
    return None


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True, type="str"),
        name=dict(required=True, type="str"),
        vlan_id=dict(required=False, type="int", default=None),
        regions=dict(required=False, type="list", elements="str", default=None),
        state=dict(choices=["present", "absent"], default="present"),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )
    client = OVH(module)

    service_name = module.params["service_name"]
    name = module.params["name"]
    state = module.params["state"]

    current = _find_network_by_name(client, service_name, name)

    # --- state: absent ---
    if state == "absent":
        if current is None:
            module.exit_json(changed=False, msg=f"Private network '{name}' does not exist")

        network_id = current["id"]
        if module.check_mode:
            module.exit_json(
                changed=True,
                msg=f"Private network '{name}' [{network_id}] would be deleted (dry run)",
            )

        client.wrap_call(
            "DELETE",
            f"/cloud/project/{service_name}/network/private/{network_id}",
        )
        module.exit_json(changed=True, msg=f"Private network '{name}' [{network_id}] deleted")

    # --- state: present ---

    # CREATE
    if current is None:
        if module.check_mode:
            module.exit_json(
                changed=True,
                msg=f"Private network '{name}' would be created (dry run)",
            )

        post_kwargs = dict(name=name)
        if module.params.get("vlan_id") is not None:
            post_kwargs["vlanId"] = module.params["vlan_id"]
        if module.params.get("regions") is not None:
            post_kwargs["regions"] = module.params["regions"]

        result = client.wrap_call(
            "POST",
            f"/cloud/project/{service_name}/network/private",
            **post_kwargs,
        )
        module.exit_json(changed=True, msg=f"Private network '{name}' created", **result)

    # ALREADY EXISTS — validate immutable fields
    network_id = current["id"]

    if module.params.get("vlan_id") is not None and current.get("vlanId") != module.params["vlan_id"]:
        module.fail_json(msg=f"Cannot change 'vlan_id' for existing private network '{name}'")

    module.exit_json(
        changed=False,
        msg=f"Private network '{name}' [{network_id}] already exists",
        **current,
    )


def main():
    run_module()


if __name__ == '__main__':
    main()
