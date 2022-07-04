#!/usr/bin/python
# -*- coding: utf-8 -*-

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
    value:
        required: true
        description: The value of the record, can be a list
    name:
        required: true
        description: The name to create/update/delete
    domain:
        required: true
        description: The domain to modify
    record_type:
        required: false
        description: The DNS record type (A AAAA CAA CNAME DKIM DMARC DNAME LOC MX NAPTR NS PTR SPF SRV SSHFP TLSA TXT)
        default: A
    state:
        required: false
        description: Indicate the desired state for the record
    append:
        required: false
        description: Keep existings values and append
        default: present
        choices:
          - present
          - absent
    ttl:
        required: false
        default: 0
        description: Time To live for the given record

'''

EXAMPLES = '''
- name: Ensure entry is in dns
  synthesio.ovh.domain:
    domain: example.com
    value: "192.2.0.1"
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
        value=dict(required=True, type="list"),
        name=dict(required=True),
        domain=dict(required=True),
        record_type=dict(choices=['A', 'AAAA', 'CAA', 'CNAME', 'DKIM', 'DMARC',
                                  'DNAME', 'LOC', 'MX', 'NAPTR', 'NS', 'PTR',
                                  'SPF', 'SRV', 'SSHFP', 'TLSA', 'TXT'],
                         default='A'),
        state=dict(choices=['present', 'absent'], default='present'),
        record_ttl=dict(type="int", required=False, default=0),
        append=dict(required=False, default=False, type="bool")
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    value = module.params['value']
    domain = module.params['domain']
    name = module.params['name']
    record_type = module.params['record_type']
    state = module.params['state']
    append = module.params['append']
    record_ttl = module.params["record_ttl"]

    if module.check_mode:
        module.exit_json(msg="{} set to {}.{} ! - (dry run mode)".format(', '.join(value), name, domain))

    try:
        existing_records = client.get(
            '/domain/zone/%s/record' % domain,
            fieldType=record_type,
            subDomain=name
        )
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    record_created = []
    record_deleted = []
    if state == 'present':

        # At least one record already exists
        if existing_records:
            for ind in existing_records:
                try:
                    record = client.get(
                        '/domain/zone/%s/record/%s' % (domain, ind)
                    )
                    # the record already exists : don't add it later
                    if record['target'] in value:
                        value.remove(record['target'])

                    # the record must not exist and append is set to false : delete from zone
                    if record['target'] not in value and not append:
                        client.delete(
                            '/domain/zone/%s/record/%s' % (domain, ind)
                        )
                        record_deleted.append(record['target'])

                except APIError as api_error:
                    module.fail_json(
                        msg="Failed to call OVH API: {0}".format(api_error))

        for v in value:
            try:
                client.post(
                    '/domain/zone/%s/record' % domain,
                    fieldType=record_type,
                    subDomain=name,
                    target=v,
                    ttl=record_ttl
                )
                record_created.append(v)
            except APIError as api_error:
                module.fail_json(
                    msg="Failed to call OVH API: {0}".format(api_error))

        if len(record_deleted) + len(record_created):
            # we must run a refresh on zone after modifications
            client.post(
                '/domain/zone/%s/refresh' % domain
            )

            msg = ''
            if len(record_deleted):
                msg += '{} deleted'.format(', '.join(record_deleted))
            if len(record_created):
                if len(record_deleted):
                    msg += ' and '
                msg += '{} created'.format(', '.join(record_created))
            msg += ' from record {}.{}'.format(name, domain)

            module.exit_json(msg=msg, changed=True)
        else:
            module.exit_json(msg="{} is already up-to-date on domain {}".format(name, domain), changed=False)

    elif state == 'absent':
        if not existing_records:
            module.exit_json(msg="Target {} doesn't exist on domain {}".format(name, domain), changed=False)

        try:
            for ind in existing_records:
                record = client.get(
                    '/domain/zone/%s/record/%s' % (domain, ind)
                )
                client.delete(
                    '/domain/zone/%s/record/%s' % (domain, ind)
                )
                record_deleted.append(record.get('target'))

            # we must run a refresh on zone after modifications
            client.post(
                '/domain/zone/%s/refresh' % domain
            )
            module.exit_json(msg='{} deleted  from record {}.{}'.format(
                ', '.join(record_deleted), name, domain), changed=True)

        except APIError as api_error:
            module.fail_json(
                msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
