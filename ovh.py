#!/usr/bin/env python

try:
	import json
except ImportError:
	import simplejson as json

import ovh

def changeDNS(ovhclient, module):
	msg = ''
	if module.params['domain'] and module.params['ip']:
		if module.params['state'] == 'present':
			result = ovhclient.post('/domain/zone/%s/record' % module.params['domain'],
					fieldType=u'A',
					subDomain=module.params['name'],
					target=module.params['ip'])
			if result['id']:
				ovhclient.post('/domain/zone/%s/refresh' % module.params['domain'])
				module.exit_json(changed=True, contents=result)
			else:
				module.fail_json(changed=False, msg="Cannot add %s to domain %s: %s" % (module.params['name'], module.params['domain'], result))
		elif module.params['state'] == 'modified':
			resultget = ovhclient.get('/domain/zone/%s/record' % module.params['domain'],
					fieldType=u'A',
					subDomain=module.params['name'])
			if resultget:
				for ind in resultget:
					resultpost = ovhclient.put('/domain/zone/%s/record/%s' % (module.params['domain'], ind),
							subDomain=module.params['name'],
							target=module.params['ip'])
					msg += '{ "fieldType": "A", "id": "%s", "subDomain": "%s", "target": "%s", "zone": "%s" } ' % (ind, module.params['name'], module.params['ip'], module.params['domain'])
				ovhclient.post('/domain/zone/%s/refresh' % module.params['domain'])
				module.exit_json(changed=True, msg=msg)
			else:
				module.fail_json(changed=False, msg="The target %s doesn't exist in domain %s" % (module.params['name'], module.params['domain']))
		elif module.params['state'] == 'absent':
			resultget = ovhclient.get('/domain/zone/%s/record' % module.params['domain'],
					fieldType=u'A',
					subDomain=module.params['name'])
			if resultget:
				for ind in resultget:
					resultpost = ovhclient.delete('/domain/zone/%s/record/%s' % (module.params['domain'], ind))
				ovhclient.post('/domain/zone/%s/refresh' % module.params['domain'])
				module.exit_json(changed=True, msg="Target %s succesfully deleted from domain %s" % (module.params['name'], module.params['domain']))
			else:
				module.exit_json(changed=False, msg="Target %s doesn't exist on domain %s" % (module.params['name'], module.params['domain']))
	else:
		if not module.params['domain']:
			module.fail_json(changed=False, msg="Please give a domain to add your target")
		if not module.params['ip']:
			module.fail_json(changed=False, msg="Please give an IP to add your target")

def main():
	module = AnsibleModule(
			argument_spec = dict(
				state = dict(default='present', choices=['present', 'absent', 'modified']),
				name  = dict(required=True),
				service = dict(choices=['dedicated', 'dns', 'vrack'], required=True),
				domain = dict(required=False, default='None'),
				ip    = dict(required=False, default='None')
				)
			)
	client = ovh.Client()
	if module.params['service'] == 'dns':
		changeDNS(client, module)

from ansible.module_utils.basic import *
if __name__ == '__main__':
	    main()
