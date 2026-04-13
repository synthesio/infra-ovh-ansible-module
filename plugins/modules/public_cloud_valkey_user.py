#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, OVHResourceNotFound, ovh_argument_spec

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_valkey_user
short_description: Manage users on an OVHcloud Managed Valkey cluster
description:
  - Create, update, or delete users on an OVHcloud Managed Valkey cluster.
  - The user is identified by its C(name). The username cannot be changed after creation.
  - ACL fields (C(categories), C(channels), C(commands), C(keys)) control what the user can access.
requirements:
  - python-ovh >= 0.5.0
options:
  service_name:
    description: Public cloud project ID.
    required: true
    type: str
  cluster_id:
    description: Valkey cluster ID (UUID).
    required: true
    type: str
  name:
    description:
      - Username. Immutable after creation.
    required: true
    type: str
  categories:
    description:
      - List of Redis command category rules (e.g. C(+@all), C(-@dangerous)).
    required: false
    type: list
    elements: str
  channels:
    description:
      - List of pub/sub channel patterns the user is allowed to access.
    required: false
    type: list
    elements: str
  commands:
    description:
      - List of specific command rules applied on top of C(categories).
    required: false
    type: list
    elements: str
  keys:
    description:
      - List of key patterns the user is allowed to access.
    required: false
    type: list
    elements: str
  state:
    description: Desired state of the user.
    choices: ['present', 'absent']
    default: present
    type: str
author:
  - Jonathan Piron <jonathan@piron.at>
'''

EXAMPLES = r'''
- name: Create a read-only user on all keys
  synthesio.ovh.public_cloud_valkey_user:
    service_name: "{{ project_id }}"
    cluster_id: "{{ cluster_id }}"
    name: readonly
    categories:
      - "+@read"
      - "-@dangerous"
    keys:
      - "*"
    state: present

- name: Create an admin user
  synthesio.ovh.public_cloud_valkey_user:
    service_name: "{{ project_id }}"
    cluster_id: "{{ cluster_id }}"
    name: admin
    categories:
      - "+@all"
    keys:
      - "*"
    channels:
      - "*"
    state: present

- name: Restrict user to a specific key prefix
  synthesio.ovh.public_cloud_valkey_user:
    service_name: "{{ project_id }}"
    cluster_id: "{{ cluster_id }}"
    name: app-user
    categories:
      - "+@read"
      - "+@write"
    keys:
      - "app:*"
    state: present

- name: Delete a user
  synthesio.ovh.public_cloud_valkey_user:
    service_name: "{{ project_id }}"
    cluster_id: "{{ cluster_id }}"
    name: readonly
    state: absent
'''

RETURN = ''' # '''


def _find_user_by_name(client, service_name, cluster_id, name):
    """Return the user dict matching the given name, or None."""
    try:
        user_ids = client.wrap_call(
            "GET",
            f"/cloud/project/{service_name}/database/valkey/{cluster_id}/user",
        )
    except OVHResourceNotFound:
        return None
    for user_id in user_ids:
        try:
            user = client.wrap_call(
                "GET",
                f"/cloud/project/{service_name}/database/valkey/{cluster_id}/user/{user_id}",
            )
        except OVHResourceNotFound:
            continue
        if user.get("username") == name:
            return user
    return None


def _build_update_params(module_params, current):
    """
    Compare desired ACL fields against the current user state.
    Return (needs_update, put_kwargs) where put_kwargs contains only changed fields.
    """
    acl_fields = {
        "categories": "categories",
        "channels": "channels",
        "commands": "commands",
        "keys": "keys",
    }

    put_kwargs = {}
    needs_update = False

    for param, api_field in acl_fields.items():
        value = module_params.get(param)
        if value is None:
            continue
        current_value = current.get(api_field, [])
        if sorted(value) != sorted(current_value):
            needs_update = True
            put_kwargs[api_field] = value

    return needs_update, put_kwargs


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True, type="str"),
        cluster_id=dict(required=True, type="str"),
        name=dict(required=True, type="str"),
        categories=dict(required=False, type="list", elements="str", default=None),
        channels=dict(required=False, type="list", elements="str", default=None),
        commands=dict(required=False, type="list", elements="str", default=None),
        keys=dict(required=False, type="list", elements="str", default=None),
        state=dict(choices=["present", "absent"], default="present"),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )
    client = OVH(module)

    service_name = module.params["service_name"]
    cluster_id = module.params["cluster_id"]
    name = module.params["name"]
    state = module.params["state"]

    current = _find_user_by_name(client, service_name, cluster_id, name)

    # --- state: absent ---
    if state == "absent":
        if current is None:
            module.exit_json(changed=False, msg=f"User '{name}' does not exist on cluster '{cluster_id}'")

        user_id = current["id"]
        if module.check_mode:
            module.exit_json(
                changed=True,
                msg=f"User '{name}' [{user_id}] would be deleted (dry run)",
            )

        client.wrap_call(
            "DELETE",
            f"/cloud/project/{service_name}/database/valkey/{cluster_id}/user/{user_id}",
        )
        module.exit_json(changed=True, msg=f"User '{name}' [{user_id}] deleted")

    # --- state: present ---

    # CREATE
    if current is None:
        if module.check_mode:
            module.exit_json(
                changed=True,
                msg=f"User '{name}' would be created on cluster '{cluster_id}' (dry run)",
            )

        post_kwargs = dict(name=name)
        for param, api_field in [
            ("categories", "categories"),
            ("channels", "channels"),
            ("commands", "commands"),
            ("keys", "keys"),
        ]:
            value = module.params.get(param)
            if value is not None:
                post_kwargs[api_field] = value

        result = client.wrap_call(
            "POST",
            f"/cloud/project/{service_name}/database/valkey/{cluster_id}/user",
            **post_kwargs,
        )
        module.exit_json(changed=True, msg=f"User '{name}' created on cluster '{cluster_id}'", **result)

    # UPDATE
    user_id = current["id"]
    needs_update, put_kwargs = _build_update_params(module.params, current)

    if not needs_update:
        module.exit_json(
            changed=False,
            msg=f"User '{name}' [{user_id}] is already up to date",
            **current,
        )

    if module.check_mode:
        module.exit_json(
            changed=True,
            msg=f"User '{name}' [{user_id}] would be updated (dry run)",
        )

    client.wrap_call(
        "PUT",
        f"/cloud/project/{service_name}/database/valkey/{cluster_id}/user/{user_id}",
        **put_kwargs,
    )
    updated = client.wrap_call(
        "GET",
        f"/cloud/project/{service_name}/database/valkey/{cluster_id}/user/{user_id}",
    )
    module.exit_json(
        changed=True,
        msg=f"User '{name}' [{user_id}] updated",
        **updated,
    )


def main():
    run_module()


if __name__ == '__main__':
    main()
