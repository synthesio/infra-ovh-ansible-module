#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, OVHResourceNotFound, ovh_argument_spec

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_valkey
short_description: Manage OVHcloud Managed Valkey clusters
description:
  - Create, update, or delete Managed Valkey clusters in an OVHcloud Public Cloud project.
  - The cluster is identified by its C(description).
  - Immutable fields (C(version), C(nodes_pattern), C(nodes_list), C(network_id), C(subnet_id))
    cannot be changed after creation.
requirements:
  - python-ovh >= 0.5.0
options:
  service_name:
    description: Public cloud project ID.
    required: true
    type: str
  description:
    description:
      - Human-readable name for the cluster. Used to identify the cluster idempotently.
    required: true
    type: str
  plan:
    description:
      - Service plan (e.g. C(essential), C(business), C(enterprise)).
      - Required when creating a cluster.
    required: false
    type: str
  version:
    description:
      - Valkey version (e.g. C(7.2)).
      - Required when creating a cluster.
      - Immutable after creation.
    required: false
    type: str
  nodes_pattern:
    description:
      - Node pattern configuration. Mutually exclusive with C(nodes_list).
      - Required when creating a cluster unless C(nodes_list) is provided.
      - Immutable after creation.
    required: false
    type: dict
    suboptions:
      flavor:
        description: Node flavor (e.g. C(db1-4)).
        type: str
        required: true
      number:
        description: Number of nodes.
        type: int
        required: true
      region:
        description: Region (e.g. C(GRA)).
        type: str
        required: true
  nodes_list:
    description:
      - Explicit list of nodes. Mutually exclusive with C(nodes_pattern).
      - Required when creating a cluster unless C(nodes_pattern) is provided.
      - Immutable after creation.
    required: false
    type: list
    elements: dict
    suboptions:
      flavor:
        description: Node flavor.
        type: str
        required: true
      region:
        description: Region.
        type: str
        required: true
  network_id:
    description:
      - Private network ID to attach the cluster to.
      - Immutable after creation.
    required: false
    type: str
  subnet_id:
    description:
      - Subnet ID within the private network.
      - Immutable after creation.
    required: false
    type: str
  ip_restrictions:
    description: List of allowed IP ranges (CIDR notation). An empty list removes all restrictions.
    required: false
    type: list
    elements: dict
    suboptions:
      ip:
        description: CIDR block (e.g. C(192.0.2.0/24)).
        type: str
        required: true
      description:
        description: Optional description for this restriction.
        type: str
  backup_time:
    description: Preferred backup time in C(HH:MM:SS) format.
    required: false
    type: str
  maintenance_time:
    description: Preferred maintenance window start time in C(HH:MM:SS) format.
    required: false
    type: str
  deletion_protection:
    description: Enable deletion protection.
    required: false
    type: bool
  enable_prometheus:
    description: Enable Prometheus metrics endpoint.
    required: false
    type: bool
  state:
    description: Desired state of the cluster.
    choices: ['present', 'absent']
    default: present
    type: str
author:
  - Jonathan Piron <jonathan@piron.at>
'''

EXAMPLES = r'''
- name: Create a single-node Valkey cluster on the public network
  synthesio.ovh.public_cloud_valkey:
    service_name: "{{ project_id }}"
    description: my-valkey
    plan: essential
    version: "7.2"
    nodes_pattern:
      flavor: db1-4
      number: 1
      region: GRA
    state: present

- name: Create a Valkey cluster on a private network
  synthesio.ovh.public_cloud_valkey:
    service_name: "{{ project_id }}"
    description: my-private-valkey
    plan: business
    version: "7.2"
    nodes_pattern:
      flavor: db1-15
      number: 3
      region: GRA
    network_id: "{{ network_id }}"
    subnet_id: "{{ subnet_id }}"
    ip_restrictions:
      - ip: 10.0.0.0/8
        description: internal
    state: present

- name: Restrict access to specific CIDRs
  synthesio.ovh.public_cloud_valkey:
    service_name: "{{ project_id }}"
    description: my-valkey
    ip_restrictions:
      - ip: 192.0.2.0/24
        description: vpn
    state: present

- name: Enable Prometheus and deletion protection
  synthesio.ovh.public_cloud_valkey:
    service_name: "{{ project_id }}"
    description: my-valkey
    enable_prometheus: true
    deletion_protection: true
    state: present

- name: Delete a Valkey cluster
  synthesio.ovh.public_cloud_valkey:
    service_name: "{{ project_id }}"
    description: my-valkey
    state: absent
'''

RETURN = ''' # '''


def _find_cluster_by_description(client, service_name, description):
    """Return the cluster dict matching the given description, or None."""
    try:
        cluster_ids = client.wrap_call("GET", f"/cloud/project/{service_name}/database/valkey")
    except OVHResourceNotFound:
        return None
    for cluster_id in cluster_ids:
        try:
            cluster = client.wrap_call(
                "GET",
                f"/cloud/project/{service_name}/database/valkey/{cluster_id}",
            )
        except OVHResourceNotFound:
            continue
        if cluster.get("description") == description:
            return cluster
    return None


def _normalize_ip_restrictions(restrictions):
    """Return a frozenset of (ip, description) tuples for comparison."""
    return frozenset(
        (r.get("ip", ""), r.get("description", ""))
        for r in (restrictions or [])
    )


def _build_update_params(module_params, current):
    """
    Compare desired module params against the current cluster state.
    Return (needs_update, put_kwargs) where put_kwargs contains only changed fields.
    """
    mutable_fields = {
        "plan": "plan",
        "backup_time": "backupTime",
        "maintenance_time": "maintenanceTime",
        "deletion_protection": "deletionProtection",
        "enable_prometheus": "enablePrometheus",
    }

    put_kwargs = {}
    needs_update = False

    for param, api_field in mutable_fields.items():
        value = module_params.get(param)
        if value is None:
            continue
        if current.get(api_field) != value:
            needs_update = True
            put_kwargs[api_field] = value

    desired_restrictions = module_params.get("ip_restrictions")
    if desired_restrictions is not None:
        current_restrictions = current.get("ipRestrictions", [])
        if _normalize_ip_restrictions(desired_restrictions) != _normalize_ip_restrictions(current_restrictions):
            needs_update = True
            put_kwargs["ipRestrictions"] = desired_restrictions

    return needs_update, put_kwargs


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True, type="str"),
        description=dict(required=True, type="str"),
        plan=dict(required=False, type="str", default=None),
        version=dict(required=False, type="str", default=None),
        nodes_pattern=dict(required=False, type="dict", default=None),
        nodes_list=dict(required=False, type="list", elements="dict", default=None),
        network_id=dict(required=False, type="str", default=None),
        subnet_id=dict(required=False, type="str", default=None),
        ip_restrictions=dict(required=False, type="list", elements="dict", default=None),
        backup_time=dict(required=False, type="str", default=None),
        maintenance_time=dict(required=False, type="str", default=None),
        deletion_protection=dict(required=False, type="bool", default=None),
        enable_prometheus=dict(required=False, type="bool", default=None),
        state=dict(choices=["present", "absent"], default="present"),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[("nodes_pattern", "nodes_list")],
        supports_check_mode=True,
    )
    client = OVH(module)

    service_name = module.params["service_name"]
    description = module.params["description"]
    state = module.params["state"]

    current = _find_cluster_by_description(client, service_name, description)

    # --- state: absent ---
    if state == "absent":
        if current is None:
            module.exit_json(changed=False, msg=f"Valkey cluster '{description}' does not exist")

        cluster_id = current["id"]
        if module.check_mode:
            module.exit_json(
                changed=True,
                msg=f"Valkey cluster '{description}' [{cluster_id}] would be deleted (dry run)",
            )

        client.wrap_call(
            "DELETE",
            f"/cloud/project/{service_name}/database/valkey/{cluster_id}",
        )
        module.exit_json(changed=True, msg=f"Valkey cluster '{description}' [{cluster_id}] deleted")

    # --- state: present ---

    # CREATE
    if current is None:
        if not module.params.get("plan"):
            module.fail_json(msg="'plan' is required when creating a Valkey cluster")
        if not module.params.get("version"):
            module.fail_json(msg="'version' is required when creating a Valkey cluster")
        if not module.params.get("nodes_pattern") and not module.params.get("nodes_list"):
            module.fail_json(msg="'nodes_pattern' or 'nodes_list' is required when creating a Valkey cluster")

        if module.check_mode:
            module.exit_json(
                changed=True,
                msg=f"Valkey cluster '{description}' would be created (dry run)",
            )

        post_kwargs = dict(
            description=description,
            plan=module.params["plan"],
            version=module.params["version"],
        )

        if module.params.get("nodes_pattern"):
            post_kwargs["nodesPattern"] = module.params["nodes_pattern"]
        else:
            post_kwargs["nodesList"] = module.params["nodes_list"]

        for param, api_field in [
            ("network_id", "networkId"),
            ("subnet_id", "subnetId"),
            ("ip_restrictions", "ipRestrictions"),
            ("backup_time", "backupTime"),
            ("maintenance_time", "maintenanceTime"),
            ("deletion_protection", "deletionProtection"),
            ("enable_prometheus", "enablePrometheus"),
        ]:
            value = module.params.get(param)
            if value is not None:
                post_kwargs[api_field] = value

        result = client.wrap_call(
            "POST",
            f"/cloud/project/{service_name}/database/valkey",
            **post_kwargs,
        )
        module.exit_json(changed=True, msg=f"Valkey cluster '{description}' created", **result)

    # UPDATE
    cluster_id = current["id"]

    immutable_checks = [
        ("version", "version"),
        ("network_id", "networkId"),
        ("subnet_id", "subnetId"),
    ]
    for param, api_field in immutable_checks:
        value = module.params.get(param)
        if value is not None and current.get(api_field) != value:
            module.fail_json(msg=f"Cannot change '{param}' for existing Valkey cluster '{description}'")

    needs_update, put_kwargs = _build_update_params(module.params, current)

    if not needs_update:
        module.exit_json(
            changed=False,
            msg=f"Valkey cluster '{description}' [{cluster_id}] is already up to date",
            **current,
        )

    if module.check_mode:
        module.exit_json(
            changed=True,
            msg=f"Valkey cluster '{description}' [{cluster_id}] would be updated (dry run)",
        )

    client.wrap_call(
        "PUT",
        f"/cloud/project/{service_name}/database/valkey/{cluster_id}",
        **put_kwargs,
    )
    updated = client.wrap_call(
        "GET",
        f"/cloud/project/{service_name}/database/valkey/{cluster_id}",
    )
    module.exit_json(
        changed=True,
        msg=f"Valkey cluster '{description}' [{cluster_id}] updated",
        **updated,
    )


def main():
    run_module()


if __name__ == '__main__':
    main()
