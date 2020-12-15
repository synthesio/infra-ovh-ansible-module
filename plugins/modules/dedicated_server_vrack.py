#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
---
module: dedicated_server_vrack
short_description: Change the vrack of a dedicated server.
description:
    - Change the vrack of a dedicated server.
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    serviceName:
        required: true
        description:
        - The server to manage
    vrack:
        required: true
        description:
            - Id of the vrack
    state:
        required: false
        default: present
        choices: ['present','absent']
        description: Indicate the desired state of vrack

'''

EXAMPLES = '''
synthesio.ovh.dedicated_server_vrack
  serviceName: {{ serviceName }}
  vrack: "{{ vrack }}"
delegate_to: localhost
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import ovh_api_connect, ovh_argument_spec

try:
    from ovh.exceptions import APIError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        serviceName=dict(required=True),
        vrack=dict(required=True),
        state=dict(choices=['present', 'absent'], default='present')
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    serviceName = module.params['serviceName']
    vrack = module.params['vrack']
    state = module.params['state']

    if module.check_mode:
        module.exit_json(
            msg="{} succesfully {} on {} - (dry run mode)".format(
                serviceName, state, vrack),
            changed=True)

    try:
        # There is no easy way to know if the server is
        # on an old or new network generation.
        # So we need to call this new route
        # to ask for virtualNetworkInterface
        # and if the answer is empty, it's on a old generation.
        # The /vrack/%s/allowedServices route used previously
        # has availability and scaling problems.
        result = client.get(
            '/dedicated/server/%s/virtualNetworkInterface' % serviceName,
            mode='vrack'
        )
    except APIError as api_error:
        module.fail_json(
            msg="Failed to call OVH API: {0}".format(api_error))

# XXX: In a near future, OVH will add the possibility to add
# multiple interfaces to the same VRACK or another one
# This code may break at this moment because
# each server will have a list of dedicatedServerInterface

    # New generation
    if len(result):
        # transform the list to a string
        server_interface = "".join(result)
        try:
            is_already_registered = client.get(
                '/vrack/%s/dedicatedServerInterfaceDetails' % vrack
            )
        except APIError as api_error:
            module.fail_json(
                msg="Failed to call OVH API: {0}".format(api_error))

        for new_server in is_already_registered:
            if new_server['dedicatedServer'] == serviceName:
                if state == 'present':
                    module.exit_json(
                        msg="{} is already registered on new {}".format(
                            serviceName, vrack),
                        changed=False)
                if state == 'absent':
                    try:
                        result = client.delete(
                            '/vrack/%s/dedicatedServerInterface/%s' % (
                                vrack, server_interface)
                        )
                        module.exit_json(
                            msg="{} has been deleted from new {}".format(
                                serviceName, vrack),
                            changed=True)
                    except APIError as api_error:
                        module.fail_json(
                            msg="Failed to call OVH API: {0}".format(api_error))

        if state == 'absent':
            module.exit_json(
                msg="{} is not present on new {}, don't remove it".format(
                    serviceName, vrack),
                changed=False)

        # Server is not yet registered on vrack, go for it
        try:
            client.post(
                '/vrack/%s/dedicatedServerInterface' % vrack,
                dedicatedServerInterface=server_interface
            )
            module.exit_json(msg="{} has been added to new {}".format(serviceName, vrack), changed=True)
        except APIError as api_error:
            return module.fail_json(
                msg="Failed to call OVH API: {0}".format(api_error))

    # Old generation
    else:
        try:
            is_already_registered = client.get(
                '/vrack/%s/dedicatedServer' % vrack
            )
        except APIError as api_error:
            module.fail_json(
                msg="Failed to call OVH API: {0}".format(api_error))

        for old_server in is_already_registered:
            if old_server == serviceName:
                if state == 'present':
                    module.exit_json(
                        msg="{} is already registered on old {}".format(
                            serviceName, vrack),
                        changed=False)
                if state == 'absent':
                    try:
                        result = client.delete(
                            '/vrack/%s/dedicatedServer/%s' % (vrack, serviceName)
                        )
                        module.exit_json(
                            msg="{} has been deleted from old {}".format(
                                serviceName, vrack),
                            changed=True)
                    except APIError as api_error:
                        module.fail_json(
                            msg="Failed to call OVH API: {0}".format(api_error))

        if state == 'absent':
            module.exit_json(
                msg="{} is not present on old {}, don't remove it".format(
                    serviceName, vrack),
                changed=False)

        # Server is not yet registered on vrack, go for it
        try:
            client.post(
                '/vrack/%s/dedicatedServer' % vrack,
                dedicatedServer=serviceName
            )
            module.exit_json(msg="{} has been added to old {}".format(serviceName, vrack), changed=True)
        except APIError as api_error:
            return module.fail_json(
                msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
