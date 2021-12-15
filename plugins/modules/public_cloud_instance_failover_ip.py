#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type


DOCUMENTATION = """
---
module: public_cloud_instance_failover_ip
short_description: Manage OVH API for public cloud: attach fail-over IP to instance
description:
    - This module manage the attachment of  fail-over IP to an OVH public Cloud instance
author: Article714 (M. Piriou, C. Guychard)
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description:
            - The named/id of the project, that can be obtained using public_cloud_project_info module
    instance_id:
        required: true
        description:
            - The instance name
    fo_ip_id:
        required: true
        description:
            - The id of the fail-over IP
    state:
        required: false
        default: present
        choices: ['present','absent']
        description: Indicate the desired state of vrack
"""

EXAMPLES = """
- name: "Attach an fail-over IP to {{ instance_id }} on public cloud OVH"
  synthesio.ovh.public_cloud_instance_failover_ip:
    instance_id: "{{ instance_id }}"
    service_name: "{{ service_name }}"
    fo_ip_id: "{{ fo_ip_id }}"
"""

RETURN = """ # """

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import (
    ovh_api_connect,
    ovh_argument_spec,
)

try:
    from ovh.exceptions import APIError

    HAS_OVH = True
except ImportError:
    HAS_OVH = False


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(
        dict(
            service_name=dict(required=True),
            fo_ip_id=dict(required=True),
            instance_id=dict(required=False),
            state=dict(choices=["present", "absent"], default="present"),
        )
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    client = ovh_api_connect(module)
    service_name = module.params["service_name"]
    fo_ip_id = module.params["fo_ip_id"]
    instance_id = module.params["instance_id"]
    state = module.params["state"]

    if module.check_mode:
        module.exit_json(
            msg="successfully (a)(de)tached ({}) IP {} to/from instance {}/{} - (dry run mode)".format(
                fo_ip_id, state, instance_id, service_name
            ),
            changed=True,
        )

    # get data about ip
    ip_data = None
    try:
        ip_data = client.get(
            "/cloud/project/{0}/ip/failover/{1}".format(service_name, fo_ip_id)
        )
    except APIError as api_error:
        module.fail_json(
            msg="Error getting failover ip data list: {0}".format(api_error)
        )

    is_already_attached = False
    if ip_data and ip_data["routedTo"] == instance_id:
        is_already_attached = True

    # Attach or detach
    if state == "present":
        if not is_already_attached:
            try:
                attach_result = client.post(
                    "/cloud/project/{0}/ip/failover/{1}/attach".format(
                        service_name, fo_ip_id
                    ),
                    instanceId=instance_id,
                )

                module.exit_json(
                    msg="Fail-over IP {} has been attached to instance {}/{}".format(
                        fo_ip_id, instance_id, service_name
                    ),
                    result=attach_result,
                    changed=True,
                )

            except APIError as api_error:
                module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

        module.exit_json(
            msg="Fail-over IP {} interface already exists on instance {}".format(
                fo_ip_id, instance_id
            ),
            changed=False,
        )

    else:
        if is_already_attached:
            module.fail_json(
                msg="NOT SUPPORTED BY API YET: Do no know how to remove fo_ip_id from instance... "
            )

        module.exit_json(
            msg="Fail-over IP {} interface does not exist on instance {}".format(
                fo_ip_id, instance_id
            ),
            changed=False,
        )


def main():
    run_module()


if __name__ == "__main__":
    main()
