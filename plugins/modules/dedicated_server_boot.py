#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: dedicated_server_boot
short_description: Change the bootid of a dedicated server.
description:
    - change the bootid and can reboot a dedicated server.
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description:
        - The server to manage
    boot:
        required: true
        default: harddisk

choices: ['harddisk','rescue-customer','ipxe-shell','poweroff']
        description:
            - Which way you want to boot your dedicated server
    force_reboot:
        required: false
        default: false
        choices: ['true','false']
        description:
            - When you want to force a dedicated server reboot

"""

EXAMPLES = r"""
- name: Change the bootid of a dedicated server to rescue
  synthesio.ovh.dedicated_server_boot:
    service_name: "{{ service_name }}"
    boot: "rescue-customer"
    force_reboot: "true"
  delegate_to: localhost
"""

RETURN = """ # """

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import (
    OVH,
    ovh_argument_spec,
)


def build_boot_list(service_name: str, client: OVH) -> dict:
    """Build a list of available boot option.
    Get available netboots, for each one fetch its ID.
    """
    netboot = dict()
    boot_ids = client.wrap_call("GET", f"/dedicated/server/{service_name}/boot")
    for boot_id in boot_ids:
        boot_infos = client.wrap_call(
            "GET", f"/dedicated/server/{service_name}/boot/{boot_id}"
        )
        if boot_infos["kernel"] == "hd":
            # The kernel parameter is "hd" in the API
            # but we use "harddisk", which is the bootType parameter
            netboot.update({"harddisk": boot_infos["bootId"]})
        else:
            netboot.update({boot_infos["kernel"]: boot_infos["bootId"]})

    return netboot


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(
        dict(
            service_name=dict(required=True),
            boot=dict(
                required=True,
                choices=["harddisk", "rescue-customer", "ipxe-shell", "poweroff"],
            ),
            force_reboot=dict(required=False, default=False, type="bool"),
        )
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    client = OVH(module)

    service_name = module.params["service_name"]
    boot = module.params["boot"]
    force_reboot = module.params["force_reboot"]
    changed = False

    bootid = build_boot_list(service_name, client)

    if boot not in list(bootid.keys()):
        module.fail_json(
            msg=f"Fail, {boot} is not in the available option: {list(bootid.keys())}"
        )

    if module.check_mode:
        message = f"{service_name} is now set to boot on {boot}."
        if force_reboot:
            message = message + " Reboot asked."
        module.exit_json(msg=f"{message} (dry run mode)")

    check = client.wrap_call("GET", f"/dedicated/server/{service_name}")

    if bootid[boot] != check["bootId"]:
        client.wrap_call(
            "PUT", f"/dedicated/server/{service_name}", bootId=bootid[boot]
        )
        changed = True

    if force_reboot:
        client.wrap_call("POST", f"/dedicated/server/{service_name}/reboot")

        module.exit_json(
            msg="{} is now forced to reboot on {}".format(service_name, boot),
            changed=True,
        )

    module.exit_json(
        msg="{} is now set to boot on {}".format(service_name, boot), changed=changed
    )


def main():
    run_module()


if __name__ == "__main__":
    main()
