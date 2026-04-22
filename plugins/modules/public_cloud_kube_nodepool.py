#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_kube_nodepool
short_description: Manage OVHcloud Managed Kubernetes node pools
description:
  - Create, update, or delete node pools in an OVHcloud Managed Kubernetes cluster.
  - The node pool is identified by its C(name). Immutable fields (C(flavor_name),
    C(anti_affinity)) cannot be changed after creation.
requirements:
  - python-ovh >= 0.5.0
options:
  service_name:
    description: Public cloud project ID.
    required: true
    type: str
  kube_id:
    description: Kubernetes cluster ID.
    required: true
    type: str
  name:
    description: Node pool name. Underscore character is not allowed.
    required: true
    type: str
  flavor_name:
    description:
      - Instance flavor designation (e.g. C(b2-7), C(b3-8)).
      - Required when creating a node pool.
      - Immutable after creation.
    required: false
    type: str
  desired_nodes:
    description: Desired number of nodes in the pool.
    required: false
    type: int
  min_nodes:
    description: Minimum number of nodes (used when autoscaling is enabled).
    required: false
    type: int
  max_nodes:
    description: Maximum number of nodes (used when autoscaling is enabled).
    required: false
    type: int
  autoscale:
    description: Enable autoscaling for the node pool.
    required: false
    type: bool
  anti_affinity:
    description:
      - Enable anti-affinity so that nodes are placed on different hypervisors.
      - Immutable after creation.
    required: false
    type: bool
  monthly_billed:
    description: Enable monthly billing (offers a discount over hourly billing).
    required: false
    type: bool
  availability_zones:
    description: List of availability zones for the node pool.
    required: false
    type: list
    elements: str
  template:
    description:
      - Node configuration template applied to all nodes in the pool.
      - Supports metadata (labels, annotations, finalizers) and spec (taints, unschedulable).
    required: false
    type: dict
    suboptions:
      metadata:
        description: Node metadata.
        type: dict
        suboptions:
          labels:
            description: Key-value labels applied to nodes.
            type: dict
          annotations:
            description: Key-value annotations applied to nodes.
            type: dict
          finalizers:
            description: List of finalizer strings.
            type: list
            elements: str
      spec:
        description: Node spec.
        type: dict
        suboptions:
          unschedulable:
            description: Prevent pods from being scheduled on nodes.
            type: bool
          taints:
            description: List of Kubernetes taints applied to nodes.
            type: list
            elements: dict
  state:
    description: Desired state of the node pool.
    choices: ['present', 'absent']
    default: present
    type: str
author:
  - Jonathan Piron <jonathan@piron.at>
'''

EXAMPLES = r'''
- name: Create a node pool
  synthesio.ovh.public_cloud_kube_nodepool:
    service_name: "{{ project_id }}"
    kube_id: "{{ kube_id }}"
    name: my-nodepool
    flavor_name: b2-7
    desired_nodes: 3
    min_nodes: 1
    max_nodes: 5
    autoscale: true
    state: present

- name: Create a node pool with labels and taints
  synthesio.ovh.public_cloud_kube_nodepool:
    service_name: "{{ project_id }}"
    kube_id: "{{ kube_id }}"
    name: gpu-nodepool
    flavor_name: t1-45
    desired_nodes: 2
    anti_affinity: true
    monthly_billed: true
    template:
      metadata:
        labels:
          gpu: "true"
          team: ml
        annotations:
          cluster-autoscaler.kubernetes.io/safe-to-evict: "false"
      spec:
        taints:
          - key: gpu
            value: "true"
            effect: NoSchedule
    state: present

- name: Scale up a node pool
  synthesio.ovh.public_cloud_kube_nodepool:
    service_name: "{{ project_id }}"
    kube_id: "{{ kube_id }}"
    name: my-nodepool
    desired_nodes: 5
    state: present

- name: Delete a node pool
  synthesio.ovh.public_cloud_kube_nodepool:
    service_name: "{{ project_id }}"
    kube_id: "{{ kube_id }}"
    name: my-nodepool
    state: absent
'''

RETURN = ''' # '''


def _find_nodepool_by_name(client, service_name, kube_id, name):
    """Return the nodepool dict matching the given name, or None."""
    nodepools = client.wrap_call(
        "GET",
        f"/cloud/project/{service_name}/kube/{kube_id}/nodepool",
    )
    for nodepool in nodepools:
        if nodepool.get("name") == name:
            return nodepool
    return None


def _build_update_params(module_params, current):
    """
    Compare desired module params against current nodepool state.
    Return (needs_update, put_kwargs) where put_kwargs contains only changed fields.
    """
    mutable_fields = {
        "desired_nodes": "desiredNodes",
        "min_nodes": "minNodes",
        "max_nodes": "maxNodes",
        "autoscale": "autoscale",
        "template": "template",
    }

    put_kwargs = {}
    needs_update = False

    for param, api_field in mutable_fields.items():
        value = module_params.get(param)
        if value is None:
            continue
        if value is not None and current.get(api_field) != value:
            needs_update = True
            put_kwargs[api_field] = value

    return needs_update, put_kwargs


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True, type="str"),
        kube_id=dict(required=True, type="str"),
        name=dict(required=True, type="str"),
        flavor_name=dict(required=False, type="str", default=None),
        desired_nodes=dict(required=False, type="int", default=None),
        min_nodes=dict(required=False, type="int", default=None),
        max_nodes=dict(required=False, type="int", default=None),
        autoscale=dict(required=False, type="bool", default=None),
        anti_affinity=dict(required=False, type="bool", default=None),
        monthly_billed=dict(required=False, type="bool", default=None),
        availability_zones=dict(required=False, type="list", elements="str", default=None),
        template=dict(required=False, type="dict", default=None),
        state=dict(choices=["present", "absent"], default="present"),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )
    client = OVH(module)

    service_name = module.params["service_name"]
    kube_id = module.params["kube_id"]
    name = module.params["name"]
    if "_" in name:
        module.fail_json(msg=f"Node pool name '{name}' cannot contain underscores")
    state = module.params["state"]

    current = _find_nodepool_by_name(client, service_name, kube_id, name)

    # --- state: absent ---
    if state == "absent":
        if current is None:
            module.exit_json(changed=False, msg=f"Node pool '{name}' does not exist")

        nodepool_id = current["id"]
        if module.check_mode:
            module.exit_json(
                changed=True,
                msg=f"Node pool '{name}' [{nodepool_id}] would be deleted (dry run)",
            )

        client.wrap_call(
            "DELETE",
            f"/cloud/project/{service_name}/kube/{kube_id}/nodepool/{nodepool_id}",
        )
        module.exit_json(changed=True, msg=f"Node pool '{name}' [{nodepool_id}] deleted")

    # --- state: present ---

    # CREATE
    if current is None:
        if not module.params.get("flavor_name"):
            module.fail_json(msg="'flavor_name' is required when creating a node pool")
        if module.params.get("desired_nodes") is None:
            module.fail_json(msg="'desired_nodes' is required when creating a node pool")

        if module.check_mode:
            module.exit_json(
                changed=True,
                msg=f"Node pool '{name}' would be created (dry run)",
            )

        post_kwargs = dict(
            name=name,
            flavorName=module.params["flavor_name"],
            desiredNodes=module.params["desired_nodes"],
        )
        for param, api_field in [
            ("min_nodes", "minNodes"),
            ("max_nodes", "maxNodes"),
            ("autoscale", "autoscale"),
            ("anti_affinity", "antiAffinity"),
            ("monthly_billed", "monthlyBilled"),
            ("availability_zones", "availabilityZones"),
            ("template", "template"),
        ]:
            value = module.params.get(param)
            if value is not None:
                post_kwargs[api_field] = value

        result = client.wrap_call(
            "POST",
            f"/cloud/project/{service_name}/kube/{kube_id}/nodepool",
            **post_kwargs,
        )
        module.exit_json(changed=True, msg=f"Node pool '{name}' created", **result)

    # UPDATE
    nodepool_id = current["id"]

    if module.params.get("flavor_name") is not None and module.params["flavor_name"] != current["flavor"]:
        module.fail_json(msg=f"Cannot change 'flavor_name' for existing node pool '{name}'")
    if module.params.get("anti_affinity") is not None and module.params["anti_affinity"] != current["antiAffinity"]:
        module.fail_json(msg=f"Cannot change 'anti_affinity' for existing node pool '{name}'")

    needs_update, put_kwargs = _build_update_params(module.params, current)

    if not needs_update:
        module.exit_json(
            changed=False,
            msg=f"Node pool '{name}' [{nodepool_id}] is already up to date",
            **current,
        )

    if module.check_mode:
        module.exit_json(
            changed=True,
            msg=f"Node pool '{name}' [{nodepool_id}] would be updated (dry run)",
        )

    client.wrap_call(
        "PUT",
        f"/cloud/project/{service_name}/kube/{kube_id}/nodepool/{nodepool_id}",
        **put_kwargs,
    )
    updated = client.wrap_call(
        "GET",
        f"/cloud/project/{service_name}/kube/{kube_id}/nodepool/{nodepool_id}",
    )
    module.exit_json(
        changed=True,
        msg=f"Node pool '{name}' [{nodepool_id}] updated",
        **updated,
    )


def main():
    run_module()


if __name__ == '__main__':
    main()
