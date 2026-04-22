#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, OVHResourceNotFound, ovh_argument_spec

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_kube_nodepool_info
short_description: Get information about OVHcloud Managed Kubernetes node pools
description:
  - Retrieve information about one or all node pools in an OVHcloud Managed Kubernetes cluster.
  - When C(nodepool_id) is provided, returns a single node pool object.
  - When only C(name) is provided, searches for a node pool by name.
  - When neither is provided, returns the list of all node pools.
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
  nodepool_id:
    description: Node pool ID. When provided, fetches that specific node pool.
    required: false
    type: str
  name:
    description: Node pool name. Used to search within the list when C(nodepool_id) is absent.
    required: false
    type: str
author:
  - Jonathan Piron <jonathan@piron.at>
'''

EXAMPLES = r'''
- name: List all node pools
  synthesio.ovh.public_cloud_kube_nodepool_info:
    service_name: "{{ project_id }}"
    kube_id: "{{ kube_id }}"

- name: Get a specific node pool by ID
  synthesio.ovh.public_cloud_kube_nodepool_info:
    service_name: "{{ project_id }}"
    kube_id: "{{ kube_id }}"
    nodepool_id: "{{ nodepool_id }}"

- name: Get a node pool by name
  synthesio.ovh.public_cloud_kube_nodepool_info:
    service_name: "{{ project_id }}"
    kube_id: "{{ kube_id }}"
    name: my-nodepool
  register: nodepool
'''

RETURN = ''' # '''


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True, type="str"),
        kube_id=dict(required=True, type="str"),
        nodepool_id=dict(required=False, type="str", default=None),
        name=dict(required=False, type="str", default=None),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )
    client = OVH(module)

    service_name = module.params["service_name"]
    kube_id = module.params["kube_id"]
    nodepool_id = module.params["nodepool_id"]
    name = module.params["name"]

    if nodepool_id:
        try:
            result = client.wrap_call(
                "GET",
                f"/cloud/project/{service_name}/kube/{kube_id}/nodepool/{nodepool_id}",
            )
        except OVHResourceNotFound:
            module.fail_json(msg=f"Node pool '{nodepool_id}' not found")
        module.exit_json(changed=False, **result)

    nodepools = client.wrap_call(
        "GET",
        f"/cloud/project/{service_name}/kube/{kube_id}/nodepool",
    )

    if name:
        for nodepool in nodepools:
            if nodepool.get("name") == name:
                module.exit_json(changed=False, **nodepool)
        module.fail_json(msg=f"Node pool '{name}' not found")

    module.exit_json(changed=False, nodepools=nodepools)


def main():
    run_module()


if __name__ == '__main__':
    main()
