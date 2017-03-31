#!/usr/bin/env python

try:
	import json
except ImportError:
	import simplejson as json

try:
	import ovh
	import ovh.exceptions
	from ovh.exceptions import APIError
except ImportError:
	module.fail_json(changed=False, msg="OVH python module required to run this module")

def getStatusInstall(ovhclient, module):
	if module.params['name']:
		try:
			result = ovhclient.get('/dedicated/server/%s/task' % module.params['name'])
			result = ovhclient.get('/dedicated/server/%s/task/%s' % (module.params['name'], max(result)))
			module.exit_json(changed=False, msg="%s" % result['status'])
		except APIError as apiError:
			module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
	else:
		module.fail_json(changed=False, msg="Please give the service's name you want to know the install status")

def launchInstall(ovhclient, module):
	if module.params['name'] and module.params['hostname'] and module.params['template']:
		details = {"details":{"language":"en","customHostname":module.params['hostname']},"templateName":module.params['template']}
		try:
			ovhclient.post('/dedicated/server/%s/install/start' % module.params['name'],
					**details)
			module.exit_json(changed=True, msg="Installation in progress on %s !" % module.params['name'])
		except APIError as apiError:
			module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
	else:
		if not module.params['name']:
			module.fail_json(changed=False, msg="Please give the service's name you want to install")
		if not module.params['template']:
			module.fail_json(changed=False, msg="Please give a template to install")
		if not module.params['hostname']:
			module.fail_json(changed=False, msg="Please give a hostname for your installation")

def changeMonitoring(ovhclient, module):
	if module.params['name'] and module.params['state']:
		if module.params['state'] == 'present':
			try:
				ovhclient.put('/dedicated/server/%s' % module.params['name'],
						monitoring=True)
				module.exit_json(changed=True, msg="Monitoring activated on %s" % module.params['name'])
			except APIError as apiError:
				module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
		elif module.params['state'] == 'absent':
			try:
				ovhclient.put('/dedicated/server/%s' % module.params['name'],
						monitoring=False)
				module.exit_json(changed=True, msg="Monitoring deactivated on %s" % module.params['name'])
			except APIError as apiError:
				module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
		else:
			module.fail_json(changed=False, msg="State modified does not match 'present' or 'absent'")
	else:
		if not module.params['name']:
			module.fail_json(changed=False, msg="Please give a name to change monitoring state")
		if not module.params['state']:
			module.fail_json(changed=False, msg="Please give a state for your monitoring")

def changeReverse(ovhclient, module):
	if module.params['domain'] and module.params['ip'] :
		fqdn = module.params['name'] + '.' + module.params['domain'] + '.'
		result = {}
		try:
			result = ovhclient.get('/ip/%s/reverse/%s' % (module.params['ip'], module.params['ip']))
		except ovh.exceptions.ResourceNotFoundError:
			result['reverse'] = ''
		if result['reverse'] != fqdn:
			try:
				ovhclient.post('/ip/%s/reverse' % module.params['ip'],
						ipReverse=module.params['ip'],
						reverse=fqdn)
				module.exit_json(changed=True, msg="Reverse %s to %s succesfully set !" % (module.params['ip'], fqdn))
			except APIError as apiError:
				module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
		else:
			module.exit_json(changed=False, msg="Reverse already set")
	else:
		if not module.params['domain']:
			module.fail_json(changed=False, msg="Please give a domain to add your target")
		if not module.params['ip']:
			module.fail_json(changed=False, msg="Please give an IP to add your target")

def changeDNS(ovhclient, module):
	msg = ''
	if module.params['name'] == 'refresh':
		try:
			ovhclient.post('/domain/zone/%s/refresh' % module.params['domain'])
			module.exit_json(changed=True, msg="Domain %s succesfully refreshed !" % module.params['domain'])
		except APIError as apiError:
			module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
	if module.params['domain'] and module.params['ip']:
		if module.params['state'] == 'present':
			try:
				check = ovhclient.get('/domain/zone/%s/record' % module.params['domain'],
						fieldType=u'A',
						subDomain=module.params['name'])
			except APIError as apiError:
				module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
			if not check:
				try:
					result = ovhclient.post('/domain/zone/%s/record' % module.params['domain'],
						fieldType=u'A',
						subDomain=module.params['name'],
						target=module.params['ip'])
					module.exit_json(changed=True, contents=result)
				except APIError as apiError:
					module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
			else:
				module.exit_json(changed=False, msg="%s is already registered in domain %s" % (module.params['name'], module.params['domain']))
		elif module.params['state'] == 'modified':
			try:
				resultget = ovhclient.get('/domain/zone/%s/record' % module.params['domain'],
						fieldType=u'A',
						subDomain=module.params['name'])
			except APIError as apiError:
				module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
			if resultget:
				try:
					for ind in resultget:
						resultpost = ovhclient.put('/domain/zone/%s/record/%s' % (module.params['domain'], ind),
									subDomain=module.params['name'],
									target=module.params['ip'])
						msg += '{ "fieldType": "A", "id": "%s", "subDomain": "%s", "target": "%s", "zone": "%s" } ' % (ind, module.params['name'], module.params['ip'], module.params['domain'])
					ovhclient.post('/domain/zone/%s/refresh' % module.params['domain'])
					module.exit_json(changed=True, msg=msg)
				except APIError as apiError:
					module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
			else:
				module.fail_json(changed=False, msg="The target %s doesn't exist in domain %s" % (module.params['name'], module.params['domain']))
		elif module.params['state'] == 'absent':
			try:
				resultget = ovhclient.get('/domain/zone/%s/record' % module.params['domain'],
						fieldType=u'A',
						subDomain=module.params['name'])
			except APIError as apiError:
				module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
			if resultget:
				try:
					for ind in resultget:
						resultpost = ovhclient.delete('/domain/zone/%s/record/%s' % (module.params['domain'], ind))
					ovhclient.post('/domain/zone/%s/refresh' % module.params['domain'])
					module.exit_json(changed=True, msg="Target %s succesfully deleted from domain %s" % (module.params['name'], module.params['domain']))
				except APIError as apiError:
					module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
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
			try:
				check = ovhclient.get('/dedicated/server/%s/vrack' % (module.params['name']))
			except APIError as apiError:
				module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
			if not check:
				try:
					result = ovhclient.post('/vrack/%s/dedicatedServer' % module.params['vrack'],
						dedicatedServer=module.params['name'])
					module.exit_json(changed=True, contents=result)
				except APIError as apiError:
					module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
			else:
				module.exit_json(changed=False, msg="%s is already registered in the vrack %s" % (module.params['name'], module.params['vrack']))
		elif module.params['state'] == 'absent':
			try:
				result = ovhclient.delete('/vrack/%s/dedicatedServer/%s' % (module.params['vrack'], module.params['name']))
				module.exit_json(changed=True, contents=result)
			except APIError as apiError:
				module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
		else:
			module.exit_json(changed=False, msg="Vrack service only uses present/absent state")
	else:
		module.fail_json(changed=False, msg="Please give a vrack name to add/remove your server")

def changeBootDedicated(ovhclient, module):
	bootid = { 'harddisk':1, 'rescue':1122 }
	try:
		check = ovhclient.get('/dedicated/server/%s' % module.params['name'])
	except APIError as apiError:
		module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
	if bootid[module.params['boot']] != check['bootId']:
		try:
			ovhclient.put('/dedicated/server/%s' % module.params['name'],
					bootId=bootid[module.params['boot']])
			ovhclient.post('/dedicated/server/%s/reboot' % module.params['name'])
			module.exit_json(changed=True, msg="%s is now set to boot on %s. Reboot in progress..." % (module.params['name'], module.params['boot']))
		except APIError as apiError:
			module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
	else:
		if module.params['force_reboot'] == 'yes' or module.params['force_reboot'] == 'true':
			try:
				ovhclient.post('/dedicated/server/%s/reboot' % module.params['name'])
			except APIError as apiError:
				module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
		module.exit_json(changed=False, msg="%s already configured for boot on %s" % (module.params['name'], module.params['boot']))

def main():
	module = AnsibleModule(
			argument_spec = dict(
				state = dict(default='present', choices=['present', 'absent', 'modified']),
				name  = dict(required=True),
				service = dict(choices=['boot', 'dns', 'vrack', 'reverse', 'monitoring', 'install', 'status'], required=True),
				domain = dict(required=False, default='None'),
				ip    = dict(required=False, default='None'),
				vrack = dict(required=False, default='None'),
				boot = dict(default='harddisk', choices=['harddisk', 'rescue']),
				force_reboot = dict(required=False, default='no', choices=BOOLEANS),
				template = dict(required=False, default='None'),
				hostname = dict(required=False, default='None')
				)
			)
	try:
		client = ovh.Client()
	except APIError as apiError:
		module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
	if module.params['service'] == 'dns':
		changeDNS(client, module)
	elif module.params['service'] == 'vrack':
		changeVRACK(client, module)
	elif module.params['service'] == 'boot':
		changeBootDedicated(client, module)
	elif module.params['service'] == 'reverse':
		changeReverse(client, module)
	elif module.params['service'] == 'monitoring':
		changeMonitoring(client, module)
	elif module.params['service'] == 'install':
		launchInstall(client, module)
	elif module.params['service'] == 'status':
		getStatusInstall(client, module)

from ansible.module_utils.basic import *
if __name__ == '__main__':
	    main()
