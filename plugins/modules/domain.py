#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: domain
short_description: Manage DNS zone
description:
    - Manage DNS zone (only A records for now)
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    ip:
        required: true
        description: The ip
    name:
        required: true
        description: The name to create/update/delete
    domain:
        required: true
        description: The domain to modify
    state:
        required: false
        description: The state

'''

EXAMPLES = '''
synthesio.ovh.domain:
  domain: example.com
  ip: "192.2.0.1"
  name: "www"
  state: "present"
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
        ip=dict(required=True),
        name=dict(required=True),
        domain=dict(required=True),
        state=dict(choices=['present', 'absent'], default='present')
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    ip = module.params['ip']
    domain = module.params['domain']
    name = module.params['name']
    state = module.params['state']

    if module.check_mode:
        module.exit_json(msg="{} set to {}.{} ! - (dry run mode)".format(ip, name, domain))

    try:
        existing_records = client.get(
            '/domain/zone/%s/record' % domain,
            fieldType='A',
            subDomain=name
        )
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    if state == 'present':

        # At least one record already exists
        if existing_records:
            for ind in existing_records:
                try:
                    record = client.get(
                        '/domain/zone/%s/record/%s' % (domain, ind)
                    )
                    # The record already exist
                    if record['subDomain'] == name and record['target'] == ip:
                        module.exit_json(
                            msg="{} is already registered on domain {}".format(name, domain),
                            changed=False)
                except APIError as api_error:
                    module.fail_json(
                        msg="Failed to call OVH API: {0}".format(api_error))

            # Gatekeeper: if more than one record match the query,
            # don't update anything and fail
            if len(existing_records) > 1:
                module.fail_json(
                    msg="More than one record match the name {} in domain {}, this module won't update all of these records.".format(name, domain))

            # Update the record if needed:
            try:
                ind = existing_records[0]
                client.put(
                    '/domain/zone/%s/record/%s' % (domain, ind),
                    subDomain=name,
                    target=ip
                )
                # we must run a refresh on zone after modifications
                client.post(
                    '/domain/zone/%s/refresh' % domain
                )
                module.exit_json(
                    msg="Record has been updated: {} is now targeting {}.{}".format(ip, name, domain), changed=True)
            except APIError as api_error:
                module.fail_json(
                    msg="Failed to call OVH API: {0}".format(api_error))

        # The record does not exist yet
        try:
            client.post(
                '/domain/zone/%s/record' % domain,
                fieldType='A',
                subDomain=name,
                target=ip
            )
            # we must run a refresh on zone after modifications
            client.post(
                '/domain/zone/%s/refresh' % domain
            )
            module.exit_json(msg="{} is now targeting {}.{}".format(ip, name, domain),
                             changed=True)
        except APIError as api_error:
            module.fail_json(
                msg="Failed to call OVH API: {0}".format(api_error))

    elif state == 'absent':
        if not existing_records:
            module.exit_json(
                msg="Target {} doesn't exist on domain {}".format(
                    name, domain),
                changed=False)

        record_deleted = []
        try:
            for ind in existing_records:
                record = client.get(
                    '/domain/zone/%s/record/%s' % (domain, ind)
                )
                client.delete(
                    '/domain/zone/%s/record/%s' % (domain, ind)
                )
                # we must run a refresh on zone after modifications
                client.post(
                    '/domain/zone/%s/refresh' % domain
                )
                record_deleted.append("%s IN A %s" % (
                    record.get('subDomain'), record.get('target')))
            module.exit_json(
                msg=",".join(record_deleted) + " successfuly deleted from domain {}".format(domain),
                changed=True)
        except APIError as api_error:
            module.fail_json(
                msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
