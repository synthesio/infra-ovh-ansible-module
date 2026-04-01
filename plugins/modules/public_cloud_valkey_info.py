#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_valkey_info
short_description: Get details of OVHcloud Managed Valkey clusters
description:
  - When C(cluster_id) is provided, fetch the properties of that single cluster.
  - When C(description) is provided, find the cluster by name and return its properties.
  - When neither is provided, fetch the properties of all clusters in the project.
  - C(cluster_id) and C(description) are mutually exclusive.
requirements:
  - python-ovh >= 0.5.0
options:
  service_name:
    description: Public cloud project ID.
    required: true
    type: str
  cluster_id:
    description: Valkey cluster ID (UUID). Mutually exclusive with C(description).
    required: false
    type: str
  description:
    description: Cluster description (name). Mutually exclusive with C(cluster_id).
    required: false
    type: str
author:
  - Synthesio SRE Team
'''

EXAMPLES = r'''
- name: Get a single Valkey cluster by ID
  synthesio.ovh.public_cloud_valkey_info:
    service_name: "{{ project_id }}"
    cluster_id: "{{ cluster_id }}"
  register: cluster_info

- name: Get a single Valkey cluster by description
  synthesio.ovh.public_cloud_valkey_info:
    service_name: "{{ project_id }}"
    description: my-valkey
  register: cluster_info

- name: Get all Valkey clusters
  synthesio.ovh.public_cloud_valkey_info:
    service_name: "{{ project_id }}"
  register: all_clusters
'''

RETURN = '''
cluster:
  description: Cluster properties. Returned when C(cluster_id) or C(description) is provided.
  returned: success, when cluster_id or description is provided
  type: dict
clusters:
  description: List of cluster properties. Returned when neither C(cluster_id) nor C(description) is provided.
  returned: success, when neither cluster_id nor description is provided
  type: list
  elements: dict
'''


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True, type="str"),
        cluster_id=dict(required=False, type="str", default=None),
        description=dict(required=False, type="str", default=None),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[("cluster_id", "description")],
        supports_check_mode=True,
    )
    client = OVH(module)

    service_name = module.params["service_name"]
    cluster_id = module.params["cluster_id"]
    description = module.params["description"]

    if cluster_id:
        cluster = client.wrap_call(
            "GET",
            f"/cloud/project/{service_name}/database/valkey/{cluster_id}",
        )
        module.exit_json(changed=False, cluster=cluster)
        return

    cluster_ids = client.wrap_call(
        "GET",
        f"/cloud/project/{service_name}/database/valkey",
    )
    all_clusters = [
        client.wrap_call("GET", f"/cloud/project/{service_name}/database/valkey/{cid}")
        for cid in cluster_ids
    ]

    if description:
        for cluster in all_clusters:
            if cluster.get("description") == description:
                module.exit_json(changed=False, cluster=cluster)
                return
        module.fail_json(msg=f"No Valkey cluster found with description '{description}'")

    module.exit_json(changed=False, clusters=all_clusters)


def main():
    run_module()


if __name__ == '__main__':
    main()
