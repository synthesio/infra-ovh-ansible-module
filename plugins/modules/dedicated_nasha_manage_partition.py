#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from urllib.parse import quote

DOCUMENTATION = """
---
module: dedicated_nasha_manage_partition
short_description: Create a nasha partition.
description:
    - Create a nasha partition with specified ACL and manage snapshots.
author: Digimind SRE Team
requirements:
    - ovh >= 0.5.0
options:
    nas_service_name:
        required: true
        description:
            - The name of the NAS
    nas_partition_name:
        required: true
        description:
            - The name of the partition you want to create
    nas_partition_size:
        required: true
        description:
            - The size of the partition you want to create in Gb. Must be >= 10 Gb
    nas_partition_description:
        required: false
        description:
            - The description of the partition
    nas_protocol:
        required: true
        choices: ['NFS', 'CIFS', 'NFS_CIFS']
        description:
            - The protocol of the partition
    nas_partition_acl:
        required: false
        type: list
        default: []
        description:
            - List of dictionaries specifying the ACLs. Each dictionary should contain the following keys
            - The IP address or CIDR range for the ACL
            - The type of ACL, either readwrite or readonly. ( Default 'readwrite')
    nas_partition_snapshot_type:
        required: false
        type: list
        default: []
        description:
            - List of snapshot types
    max_retry:
        required: false
        description: Number of retry
        default: 120
    sleep:
        required: false
        description: Time to sleep between retries
        default: 5
"""

EXAMPLES = """
- name: Create a nasha partition with specified ACL and configure snapshot
  synthesio.ovh.dedicated_nasha_manage_partition:
    nas_service_name: "{{ nas_service_name }}"
    nas_partition_name: "{{ nas_partition_name }}"
    nas_partition_size: 10
    nas_partition_description: "My Partition for my backup"
    nas_protocol: NFS
    nas_partition_acl:
      - ip: XX.XX.XX.XX/32
        type: readwrite
        state: present
      - ip: XX.XX.XX.XX/32
        type: readonly
        state: present
      - ip: XX.XX.XX.XX/32
    nas_partition_snapshot_type:
      - type: hour-1
        state: absent
      - type: day-1
        state: present
    state: "{{ state }}"
    sleep: 5
    max_retry: 120
"""

RETURN = """
changed:
    description: Indicates whether the module made any changes.
    type: bool
"""

# TODO:
# 1. Manage properties of NASHA : dedicated/nasha/{servicename} , monitored=True
# 1. Manage option of partition : dedicated/nasha/{servicename}/partition/{partitionname}/options
#    {atime: "off", recordsize: "131072", sync: "disabled"} // {atime: "on", recordsize: "131072", sync: "always"}
# 1. manage changes in size, description or protocol

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import (
    ovh_api_connect,
    ovh_argument_spec,
)
import time


try:
    from ovh.exceptions import APIError, ResourceNotFoundError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False


def wait_for_tasks_to_complete(client, storage, service, task_id, sleep, max_retry):
    i = 0
    waitForCompletion = True
    while waitForCompletion and i < float(max_retry):
        waitForCompletion = False
        try:
            task_info = client.get(f"/dedicated/{storage}/{service}/task/{task_id}")
            if task_info["status"] != "done":
                waitForCompletion = True
                print(
                    f"Task {task_id} is in {task_info['status']} status, waiting for its completion...[i:{i}]"
                )
        except APIError:
            # The taskId does not exist anymore
            continue
        if waitForCompletion:
            time.sleep(float(sleep))
        i += 1


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(
        dict(
            nas_service_name=dict(required=True),
            nas_partition_name=dict(required=True),
            nas_partition_description=dict(required=False),
            nas_partition_size=dict(required=True),
            nas_protocol=dict(required=True, choices=["NFS", "CIFS", "NFS_CIFS"]),
            nas_partition_acl=dict(required=False, type="list", default=[]),
            nas_partition_snapshot_type=dict(required=False, type="list", defaults=[]),
            state=dict(required=False, default="present"),
            max_retry=dict(required=False, default=120),
            sleep=dict(required=False, default=5),
        )
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    client = ovh_api_connect(module)

    nas_service_name = module.params["nas_service_name"]
    nas_partition_name = module.params["nas_partition_name"]
    nas_partition_description = module.params["nas_partition_description"]
    nas_partition_size = module.params["nas_partition_size"]
    if int(nas_partition_size) < 10:
        module.fail_json(msg="Partition size must be greater than or equal to 10 Gb.")
    nas_protocol = module.params["nas_protocol"]
    nas_partition_acl = module.params["nas_partition_acl"]
    nas_partition_snapshot_type = module.params["nas_partition_snapshot_type"]
    state = module.params["state"]
    max_retry = module.params["max_retry"]
    sleep = module.params["sleep"]

    # Message that will be sent at the end of execution
    final_message = ""
    DRY_RUN_MSG = ""

    if module.check_mode:
        DRY_RUN_MSG = " - (dry run mode)"

    #***************** PARTITION MANAGEMENT *****************

    # Check if zpool exist !
    try:
        client.get("/dedicated/nasha/{0}".format(nas_service_name))
    except (APIError, ResourceNotFoundError) as api_error:
        module.fail_json(
            msg="Failed to find nasha %s : %s" % (nas_service_name, api_error)
        )

    # Partitions of nas
    try:
        partitions = client.get(
            "/dedicated/nasha/{0}/partition".format(nas_service_name)
        )
    except APIError as api_error:
        module.fail_json(msg="Failed to get partitions: %s" % api_error)

    # If partition state is absent, we delete it and exit module execution
    if state == "absent" and nas_partition_name in partitions:
        if not module.check_mode:
            try:
                # Delete the partition
                client.delete(
                    "/dedicated/nasha/{0}/partition/{1}".format(
                        nas_service_name, nas_partition_name
                    )
                )
            except APIError as api_error:
                module.fail_json(msg="Failed to delete partition: %s" % api_error)

        module.exit_json(
            msg="Partition {0} has been deleted.{1}\n".format(
                nas_partition_name, DRY_RUN_MSG
            ),
            changed=True,
        )

    # If partition state is present, and does not exists, we create it
    elif state == "present" and not nas_partition_name in partitions:
        if not module.check_mode:
            try:
                # Create partition
                res = client.post(
                    "/dedicated/nasha/{0}/partition".format(nas_service_name),
                    partitionDescription=nas_partition_description,
                    partitionName=nas_partition_name,
                    protocol=nas_protocol,
                    size=nas_partition_size,
                )
                wait_for_tasks_to_complete(
                    client, "nasha", nas_service_name, res["taskId"], sleep, max_retry
                )
            except APIError as api_error:
                module.fail_json(msg="Failed to create partition: %s" % api_error)

        final_message = "Partition {0} has been created.\n".format(
            nas_partition_name,
        )
        partition_changed = True

    # If partition state is present, and partition exist
    # TODO: manage changes in size, description or protocol
    elif state == "present" and nas_partition_name in partitions:
        final_message = "Partition {0} is already created.\n".format(
            nas_partition_name
        )
        partition_changed = False

    # If partition state is absent,  and does not exists
    elif state == "absent" and not nas_partition_name in partitions:
        module.exit_json(
            msg="Partition {0} is already deleted.{1}".format(
                nas_partition_name, DRY_RUN_MSG
            ),
            changed=False,
        )

    #***************** SNAPSHOT MANAGEMENT *****************

    # If nas_partition_snapshot_type exists and not empty
    if nas_partition_snapshot_type:
        # Snapshot that already exists for partition
        nas_partition_snapshot_existing = []
        # Wanted snapshots
        nas_partition_snapshot_wanted = nas_partition_snapshot_type

        # Get all snapshots of partition
        try:
            nas_partition_snapshot_existing = client.get(
                "/dedicated/nasha/{0}/partition/{1}/snapshot".format(
                    nas_service_name, nas_partition_name
                )
            )
        except (APIError, ResourceNotFoundError) as api_error:
            module.fail_json(
                msg="Failed to get snapshots list on partition %s : %s"
                % (nas_partition_name, api_error)
            )

        # Init nas_partition_snapshot matrix
        nas_partition_snapshot = [
            {'type': 'day-1', 'current_state': 'unknown', 'wanted_state': 'unknown', 'action': ''},
            {'type': 'day-2', 'current_state': 'unknown', 'wanted_state': 'unknown', 'action': ''},
            {'type': 'day-3', 'current_state': 'unknown', 'wanted_state': 'unknown', 'action': ''},
            {'type': 'day-7', 'current_state': 'unknown', 'wanted_state': 'unknown', 'action': ''},
            {'type': 'hour-1', 'current_state': 'unknown', 'wanted_state': 'unknown', 'action': ''},
            {'type': 'hour-6', 'current_state': 'unknown', 'wanted_state': 'unknown', 'action': ''}
        ]

        res = []

        # Update wanted_state in nas_partition_snapshot
        for wanted in nas_partition_snapshot_wanted:
            for snapshot in nas_partition_snapshot:
                if snapshot["type"] == wanted["type"]:
                    snapshot["wanted_state"] = wanted.get("state", "present")

        # Update current_state in nas_partition_snapshot
        for snapshot in nas_partition_snapshot:
            if snapshot["type"] in nas_partition_snapshot_existing:
                snapshot["current_state"] = "present"
            else:
                snapshot["current_state"] = "absent"

            # Update actions
            current_state = snapshot["current_state"]
            wanted_state = snapshot["wanted_state"]

            if (
                current_state == wanted_state
                or wanted_state == "unknown"
            ):
                snapshot["action"] = "unchanged"
            elif current_state == "present" and wanted_state == "absent":
                snapshot["action"] = "delete"
            elif current_state == "absent" and wanted_state == "present":
                snapshot["action"] = "create"

            # Modify snapshots according to snapshot action
            if not module.check_mode:
                # Delete snapshots
                if snapshot["action"] == "delete":
                    try:
                        res = client.delete(
                            "/dedicated/nasha/{0}/partition/{1}/snapshot/{2}".format(
                                nas_service_name,
                                nas_partition_name,
                                snapshot.get("type"),
                            )
                        )

                    except APIError as api_error:
                        module.fail_json(
                            msg="Failed to delete snapshot %s on partition %s : %s"
                            % (snapshot.get("type"), nas_partition_name, api_error)
                        )

                    # Wait for tasks to complete
                    wait_for_tasks_to_complete(
                        client, "nasha", nas_service_name, res["taskId"], sleep, max_retry
                    )

                # Add snapshots
                elif snapshot["action"] == "create":
                    try:
                        res = client.post(
                            "/dedicated/nasha/{0}/partition/{1}/snapshot".format(
                                nas_service_name, nas_partition_name
                            ),
                            snapshotType=snapshot.get("type"),
                        )

                    except APIError as api_error:
                        module.fail_json(
                            msg="Failed to configure partition snapshot %s on %s : %s"
                            % (
                                nas_partition_snapshot_wanted,
                                nas_partition_name,
                                api_error,
                            )
                        )
                    # Wait for tasks to complete
                    wait_for_tasks_to_complete(
                        client, "nasha", nas_service_name, res["taskId"], sleep, max_retry
                    )

        nas_partition_snapshot_changed = [(item.get('type'), item.get('action')) for item in nas_partition_snapshot if item.get('action') != 'unchanged']
        if len(nas_partition_snapshot_changed) == 0:
            final_message = (final_message
                             + " No changes in snapshot configuration.\n"
                             )
        else:
            final_message = (
                final_message
                + " And setup snapshot like this {0}\n".format(
                    nas_partition_snapshot_changed,
                )
            )
            snapshot_changed = True
    else:
        final_message = (
            final_message
            + " No snapshot specified.\n"
        )


    #***************** ACL MANAGEMENT *****************

    if nas_partition_acl:
        nas_partition_acl_existing = []
        try:
            # Get existing IP ACL lists ( just IP )
            nas_partition_acl_existing_acls = client.get(
                "/dedicated/nasha/{0}/partition/{1}/access".format(
                    nas_service_name, nas_partition_name
                )
            )

            # Get existing ACL of each IP and populate a list of dict
            for ip in nas_partition_acl_existing_acls:
                try:
                    nas_partition_acl_existing_acl_properties = client.get(
                        "/dedicated/nasha/{0}/partition/{1}/access/{2}".format(
                            nas_service_name, nas_partition_name, quote(ip, safe='')
                        )
                    )
                    nas_partition_acl_existing.append(nas_partition_acl_existing_acl_properties)

                except (APIError, ResourceNotFoundError):
                    pass

        except (APIError, ResourceNotFoundError):
            pass

        nas_partition_acl_wanted = nas_partition_acl
        for acl_wanted in nas_partition_acl_wanted:
            acl_wanted.setdefault("state", "present")
            acl_wanted.setdefault("action", "unknow")
            if acl_wanted["state"] == "present":
                acl_wanted.setdefault("type", "readwrite")
            elif acl_wanted["state"] == "absent" and 'type' in acl_wanted:
                del acl_wanted["type"]

        for acl_wanted in nas_partition_acl_wanted:
            matching_acl = next((acl for acl in nas_partition_acl_existing if acl["ip"] == acl_wanted["ip"] ), None)
            if matching_acl:
                if "type" in acl_wanted:
                    if matching_acl["type"] == acl_wanted["type"] and acl_wanted["state"] == "present":
                        acl_wanted["action"] = "unchanged"
                    else:
                        acl_wanted["action"] = "update"
                else:
                    acl_wanted["action"] = "update" if acl_wanted["state"] != "absent" else "delete"
            else:
                if acl_wanted["state"] == "absent":
                    acl_wanted["action"] = "delete"
                else:
                    acl_wanted["action"] = "create"


        # Executing actions on ACLs
        for acl_wanted in nas_partition_acl_wanted:

            if acl_wanted["action"] == "delete":
                # Delete ACL on acl_wanted["ip"]
                if not module.check_mode:
                    try:
                        res = client.delete(
                            "/dedicated/nasha/{0}/partition/{1}/access/{2}".format(
                                nas_service_name,
                                nas_partition_name,
                                quote(acl_wanted["ip"], safe=''),
                            )
                        )

                        wait_for_tasks_to_complete(
                            client,
                            "nasha",
                            nas_service_name,
                            res["taskId"],
                            sleep,
                            max_retry,
                        )

                    except APIError as api_error:
                        module.fail_json(
                            msg="Failed to delete partition ACL: %s" % api_error
                        )

            elif acl_wanted["action"] == "update" or acl_wanted["action"] == "create":
                # Create or Update ACL
                if not module.check_mode:
                    try:
                        res = client.post(
                            "/dedicated/nasha/{0}/partition/{1}/access".format(
                                nas_service_name, nas_partition_name
                            ),
                            ip=acl_wanted["ip"],
                            type=acl_wanted["type"],
                        )
                        wait_for_tasks_to_complete(
                            client,
                            "nasha",
                            nas_service_name,
                            res["taskId"],
                            sleep,
                            max_retry,
                        )

                    except APIError as api_error:
                        module.fail_json(
                            msg="Failed to set partition ACL: %s" % api_error
                        )


        nas_partition_acl_changed = [(item.get('ip'), item.get('action')) for item in nas_partition_acl_wanted if item.get('action') != 'unchanged']
        if len(nas_partition_acl_changed) == 0:
            final_message = (final_message
                             + " No changes in ACL configuration.\n"
                             )
        else:
            final_message = (
                final_message
                + " And setup ACL like this {0}\n".format(
                    nas_partition_acl_changed,
                )
            )
            acl_changed = True
    else:
        final_message = (
            final_message
            + " No ACL specified.\n"
        )

    if ('acl_changed' in locals() and acl_changed) or ('partition_changed' in locals() and partition_changed) or ('snapshot_changed' in locals() and snapshot_changed) :
        all_changed = True
    else:
        all_changed = False

    module.exit_json(
        msg=final_message + "{0}\n".format(
            DRY_RUN_MSG
        ),
        changed=all_changed,
    )


def main():
    if not HAS_OVH:
        raise ImportError("ovh Python module is required for this script")

    run_module()


if __name__ == "__main__":
    main()
