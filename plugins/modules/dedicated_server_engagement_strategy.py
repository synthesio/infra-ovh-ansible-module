from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: dedicated_server_engagement_strategy
short_description: Sets the engagement strategy for a dedicated server
description:
    - This module sets the engagement strategy for a dedicated server. 
      the engagement strategy is the rule that will be applied at the end of the current engagement period, if any.
      Possible values are:
      REACTIVATE_ENGAGEMENT
      STOP_ENGAGEMENT_FALLBACK_DEFAULT_PRICE
      CANCEL_SERVICE
author: Marco Sarti <m.sarti@onetag.com>
requirements:
    - ovh >= 0.5.0
options:
    engagement_strategy:
        required: true
        description:
            - The engagement strategy
    service_name:
        required: true
        description:
            - The service_name
'''

EXAMPLES = r'''
- name: "Changes the engagement strategy for the service"
  synthesio.ovh.dedicated_server_engagement_strategy:
    engagement_strategy: "{{ engagement_strategy }}"
    service_name: "{{ service_name }}"
  delegate_to: localhost
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        engagement_strategy=dict(required=True),
        service_name=dict(required=True)
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = OVH(module)

    engagement_strategy = module.params['engagement_strategy']
    service_name = module.params['service_name']

    if module.check_mode:
        module.exit_json(msg="engagement_strategy has been set to {} ! - (dry run mode)".format(engagement_strategy), changed=True)

    result = client.wrap_call("GET", f"/dedicated/server/{service_name}/serviceInfos")

    service_id = result["serviceId"]

    service = client.wrap_call("GET", f"/services/{service_id}")

    if service['billing']['engagement'] is None:
        module.exit_json(msg="No engagement for server {}".format(service_name), changed=False)

    if service['billing']['engagement']['strategy'] == engagement_strategy:
        module.exit_json(msg="Engagement strategy is already {} on {}"
                         .format(engagement_strategy, service_name), changed=False)

    if engagement_strategy not in service['billing']['engagement']['possibleStrategies']:
        module.fail_json(msg="Strategy {} not available for service".format(engagement_strategy))

    resource = {'strategy': engagement_strategy}

    client.wrap_call(
        "PUT",
        f"/services/{service_id}/billing/engagement/endRule",
        **resource
    )
    module.exit_json(
        msg="engagement_strategy succesfully set to {} for {} !".format(engagement_strategy, service_name),
        changed=True)


def main():
    run_module()


if __name__ == '__main__':
    main()
