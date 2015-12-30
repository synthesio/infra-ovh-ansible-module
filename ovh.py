#!/usr/bin/env python

try:
	import json
except ImportError:
	import simplejson as json

import ovh

def changeDNS(ovhclient, module):
	msg = ''
	if module.params['name'] == 'refresh':
		ovhclient.post('/domain/zone/%s/refresh' % module.params['domain'])
		module.exit_json(changed=True, msg="Domain %s succesfully refreshed !" % module.params['domain'])
	if module.params['domain'] and module.params['ip']:
		if module.params['state'] == 'present':
			check = ovhclient.get('/domain/zone/%s/record' % module.params['domain'],
					fieldType=u'A',
					subDomain=module.params['name'])
			if not check:
				result = ovhclient.post('/domain/zone/%s/record' % module.params['domain'],
						fieldType=u'A',
						subDomain=module.params['name'],
						target=module.params['ip'])
				if result['id']:
					#ovhclient.post('/domain/zone/%s/refresh' % module.params['domain'])
					module.exit_json(changed=True, contents=result)
				else:
					module.fail_json(changed=False, msg="Cannot add %s to domain %s: %s" % (module.params['name'], module.params['domain'], result))
			else:
				module.exit_json(changed=False, msg="%s is already registered in domain %s" % (module.params['name'], module.params['domain']))
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

def changeVRACK(ovhclient, module):
	if module.params['vrack']:
		if module.params['state'] == 'present':
			check = ovhclient.get('/vrack/%s/dedicatedServer/%s' % (module.params['vrack'], module.params['name']))
			if not check['vrack']:
				result = ovhclient.post('/vrack/%s/dedicatedServer' % module.params['vrack'],
						dedicatedServer=module.params['name'])
				if result['id']:
					module.exit_json(changed=True, contents=result)
				else:
					module.fail_json(changed=False, msg="Cannot add %s to the vrack %s: %s" % (module.params['name'], module.params['vrack'], result))
			else:
				module.exit_json(changed=False, msg="%s is already registred in the vrack %s" % (module.params['name'], module.params['vrack']))
		elif module.params['state'] == 'absent':
			result = ovhclient.delete('/vrack/%s/dedicatedServer/%s' % (module.params['vrack'], module.params['name']))
			if result['id']:
				module.exit_json(changed=True, contents=result)
			else:
				module.fail_json(changed=False, msg="Cannot remove %s from the vrack %s: %s" % (module.params['name'], module.params['vrack'], result))
		else:
			module.exit_json(changed=False, msg="Vrack service only uses present/absent state")
	else:
		module.fail_json(changed=False, msg="Please give a vrack name to add/remove your server")

#def changeDedicated(ovhclient, module):


def main():
	module = AnsibleModule(
			argument_spec = dict(
				state = dict(default='present', choices=['present', 'absent', 'modified']),
				name  = dict(required=True),
				service = dict(choices=['dedicated', 'dns', 'vrack'], required=True),
				domain = dict(required=False, default='None'),
				ip    = dict(required=False, default='None'),
				vrack = dict(required=False, default='None')
				)
			)
	client = ovh.Client()
	if module.params['service'] == 'dns':
		changeDNS(client, module)
	elif module.params['service'] == 'vrack':
		changeVRACK(client, module)
	#elif module.params['service'] == 'dedicated':
	#	changeDedicated(client, module)

from ansible.module_utils.basic import *
if __name__ == '__main__':
	    main()
