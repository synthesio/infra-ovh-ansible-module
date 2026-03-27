#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, OVHResourceNotFound, ovh_argument_spec

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_kube_info
short_description: Get information about OVHcloud Managed Kubernetes clusters
description:
  - Retrieve information about one or all Managed Kubernetes clusters in a public cloud project.
  - When C(kube_id) is provided, fetches that specific cluster directly.
  - When C(name) is provided, searches for a cluster by name across the list.
  - When neither is provided, returns the list of all clusters.
requirements:
  - python-ovh >= 0.5.0
options:
  service_name:
    description: Public cloud project ID.
    required: true
    type: str
  kube_id:
    description: Kubernetes cluster ID. When provided, fetches that specific cluster.
    required: false
    type: str
  name:
    description: Cluster name. Used to search within the list when C(kube_id) is absent.
    required: false
    type: str
author:
  - Jonathan Piron <jonathan@piron.at>
'''

EXAMPLES = r'''
- name: List all Kubernetes clusters
  synthesio.ovh.public_cloud_kube_info:
    service_name: "{{ project_id }}"

- name: Get a specific cluster by ID
  synthesio.ovh.public_cloud_kube_info:
    service_name: "{{ project_id }}"
    kube_id: "{{ kube_id }}"

- name: Get a cluster by name and retrieve its ID
  synthesio.ovh.public_cloud_kube_info:
    service_name: "{{ project_id }}"
    name: my-cluster
  register: kube

- name: Use the retrieved cluster ID
  synthesio.ovh.public_cloud_kube_nodepool_info:
    service_name: "{{ project_id }}"
    kube_id: "{{ kube.id }}"
'''

RETURN = ''' # '''


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True, type="str"),
        kube_id=dict(required=False, type="str", default=None),
        name=dict(required=False, type="str", default=None),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )
    client = OVH(module)

    service_name = module.params["service_name"]
    kube_id = module.params["kube_id"]
    name = module.params["name"]

    if kube_id:
        try:
            result = client.wrap_call(
                "GET",
                f"/cloud/project/{service_name}/kube/{kube_id}",
            )
        except OVHResourceNotFound:
            module.fail_json(msg=f"Kubernetes cluster '{kube_id}' not found")
        module.exit_json(changed=False, **result)

    kube_ids = client.wrap_call(
        "GET",
        f"/cloud/project/{service_name}/kube",
    )

    clusters = [
        client.wrap_call("GET", f"/cloud/project/{service_name}/kube/{kid}")
        for kid in kube_ids
    ]

    if name:
        for cluster in clusters:
            if cluster.get("name") == name:
                module.exit_json(changed=False, **cluster)
        module.fail_json(msg=f"Kubernetes cluster '{name}' not found")

    module.exit_json(changed=False, clusters=clusters)


def main():
    run_module()


if __name__ == '__main__':
    main()
