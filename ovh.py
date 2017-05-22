#!/usr/bin/env python

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'supported_by': 'community',
    'status': ['preview']
		}

DOCUMENTATION = '''
---
module: ovh
short_description: Manage OVH API for DNS, monitoring and Dedicated servers
description:
	- Add/Delete/Modify entries in OVH DNS
	- Add reverse on OVH dedicated servers
	- Install new dedicated servers from a personal template only
	- Create a personal OVH template from a file
	- Monitor installation status on dedicated servers
	- Add/Remove OVH Monitoring on dedicated servers
	- Add/Remove a dedicated server from a OVH vrack
	- Restart a dedicate server on debian rescue or disk
	- List dedicated servers, personal templates
author: Francois BRUNHES aka fanfan (@synthesio)
notes:
	- In /etc/ovh.conf (on host that executes module), you should add your
	  OVH API credentials like:
	  [default]
	  ; general configuration: default endpoint
	  endpoint=ovh-eu

	  [ovh-eu]
	  ; configuration specific to 'ovh-eu' endpoint
	  application_key=<YOUR APPLICATION KEY>
	  application_secret=<YOUR APPLICATIOM SECRET>
	  consumer_key=<YOUR CONSUMER KEY>
requirements:
	- ovh > 0.3.5
options:
	name:
		required: true
		description: The name of the service (dedicated, dns)
	state:
		required: false
		default: present
		choices: ['present', 'absent', 'modified']
		description:
			- Determines whether the dedicated/dns is to be created/modified
			  or deleted
	service:
		required: true
		choices: ['boot', 'dns', 'vrack', 'reverse', 'monitoring', 'install', 'status', 'list']
		description:
			- Determines the service you want to use in the module
			  boot, change the bootid and can reboot the dedicated server
			  dns, manage A entries in your domain
			  vrack, add or remove a dedicated from a vrack
			  reverse, add/modify a reverse on a dedicated server
			  monitoring, add/removing a dedicated server from OVH monitoring
			  install, install from a template
			  status, used after install to know install status
			  list, get a list of personal dedicated servers, personal templates
	domain:
		required: false
		default: None
		description:
			- The domain used in dns and reverse services
	ip:
		required: false
		default: None
		description:
			- The public IP used in reverse and dns services
	vrack:
		required: false
		default: None
		description:
			- The vrack ID used in vrack service
	boot:
		required: false
		default: harddisk
		choices: ['harddisk','rescue']
		description:
			- Which way you want to boot your dedicated server
	force_reboot:
		required: false
		default: no
		choices: ['yes','no','true','false']
		description:
			- When you want to restart a dedicated server without changing his boot mode
	template:
		required: false
		default: None
		description:
			- One of your personal template on OVH
	hostname:
		required: false
		default: None
		description:
			- The hostname you want to replace in /etc/hostname when applying a template

'''

EXAMPLES = '''
# Add a host into the vrack
- name: Add server to vrack
  ovh: service='vrack' vrack='VRACK ID' name='HOSTNAME'

# Add a DNS entry for `internal.bar.foo.com`
- name: Add server IP to DNS
  ovh: service='dns' domain='foo.com' ip='1.2.3.4' name='internal.bar'

- name: Refresh domain
  ovh: service='dns' name='refresh' domain='{{ domain }}'

# Change a server reverse
- name: Change Reverse on server
  ovh: service=reverse name='internal.bar' ip='1.2.3.4' domain='foo.com'

# Install a server from a template
- name: Install the dedicated server
  ovh: service='install' name='foo.ovh.eu' hostname='internal.bar.foo.com' template='SOME TEMPLATE'

- name: Wait until installation is finished
  local_action:
    module: ovh
    service: status
    name: 'foo.ovh.eu'
  register: result
  until: result.msg.find("done") != -1
  retries: 150
  delay: 10

# Enable / disable OVH monitoring
- name: Remove ovh monitoring when necessary
  ovh: service='monitoring' name='foo.ovh.eu' state='present / absent'

# List personal dedicated servers
- name: Get list of servers
  ovh: service='list' name='dedicated'
  register: servers

# List personal templates
- name: Get list of personal templates
  ovh: service='list' name='templates'
  register: templates
'''

RETURN = ''' # '''

try:
	import json
except ImportError:
	import simplejson as json

try:
	import ovh
	import ovh.exceptions
	from ovh.exceptions import APIError
	HAS_OVH = True
except ImportError:
	HAS_OVH = False

def getStatusInstall(ovhclient, module):
	if module.params['name']:
		if module.check_mode:
			module.exit_json(changed=False, msg="done - (dry run mode)")
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
		try:
			result = ovhclient.get('/me/installationTemplate')
			if module.params['template'] not in result:
				module.fail_json(changed=False, msg="%s doesn't exist in personal templates" % module.params['template'])
		except APIError as apiError:
			module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
		if module.check_mode:
			module.exit_json(changed=True, msg="Installation in progress on %s ! - (dry run mode)" % module.params['name'])
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
		if module.check_mode:
			module.exit_json(changed=True, msg="Monitoring %s on %s - (dry run mode)" % (module.params['state'], module.params['name']))
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
			module.fail_json(changed=False, msg="State %s does not match 'present' or 'absent'" % module.params['state'])
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
			if module.check_mode:
				module.exit_json(changed=True, msg="Reverse %s to %s succesfully set ! - (dry run mode)" % (module.params['ip'], fqdn))
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
		if module.check_mode:
			module.exit_json(changed=True, msg="Domain %s succesfully refreshed ! - (dry run mode)" % module.params['domain'])
		try:
			ovhclient.post('/domain/zone/%s/refresh' % module.params['domain'])
			module.exit_json(changed=True, msg="Domain %s succesfully refreshed !" % module.params['domain'])
		except APIError as apiError:
			module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
	if module.params['domain'] and module.params['ip']:
		if module.check_mode:
			module.exit_json(changed=True, msg="DNS succesfully %s on %s - (dry run mode)" % (module.params['state'], module.params['name']))
		try:
			check = ovhclient.get('/domain/zone/%s/record' % module.params['domain'],
						fieldType=u'A',
						subDomain=module.params['name'])
		except APIError as apiError:
			module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
		if module.params['state'] == 'present':
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
			if check:
				try:
					for ind in check:
						resultpost = ovhclient.put('/domain/zone/%s/record/%s' % (module.params['domain'], ind),
									subDomain=module.params['name'],
									target=module.params['ip'])
						msg += '{ "fieldType": "A", "id": "%s", "subDomain": "%s", "target": "%s", "zone": "%s" } ' % (ind, module.params['name'], module.params['ip'], module.params['domain'])
					module.exit_json(changed=True, msg=msg)
				except APIError as apiError:
					module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
			else:
				module.fail_json(changed=False, msg="The target %s doesn't exist in domain %s" % (module.params['name'], module.params['domain']))
		elif module.params['state'] == 'absent':
			if check:
				try:
					for ind in check:
						resultpost = ovhclient.delete('/domain/zone/%s/record/%s' % (module.params['domain'], ind))
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
		if module.check_mode:
			module.exit_json(changed=True, msg="%s succesfully %s on %s - (dry run mode)" % (module.params['name'], module.params['state'],module.params['vrack']))
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
	if module.check_mode:
		module.exit_json(changed=True, msg="%s is now set to boot on %s. Reboot in progress... - (dry run mode)" % (module.params['name'], module.params['boot']))
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

def listDedicated(ovhclient, module):
	customlist = []
	try:
		result = ovhclient.get('/dedicated/server')
	except APIError as apiError:
		module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
	try:
		for i in result:
			test = ovhclient.get('/dedicated/server/%s' % i)
			customlist.append('%s=%s' % (test['reverse'], i))
	except APIError as apiError:
		module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
	module.exit_json(changedFalse=False, objects=customlist)

def listTemplates(ovhclient, module):
        customlist = []
        try:
                result = ovhclient.get('/me/installationTemplate')
        except APIError as apiError:
                module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
        try:
                for i in result:
			if 'tmp-mgr' not in i:
                        	customlist.append(i)
        except APIError as apiError:
                module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
        module.exit_json(changedFalse=False, objects=customlist)

def main():
	module = AnsibleModule(
			argument_spec = dict(
				state = dict(default='present', choices=['present', 'absent', 'modified']),
				name  = dict(required=True),
				service = dict(choices=['boot', 'dns', 'vrack', 'reverse', 'monitoring', 'install', 'status', 'list', 'create_template', required=True),
				domain = dict(required=False, default='None'),
				ip    = dict(required=False, default='None'),
				vrack = dict(required=False, default='None'),
				boot = dict(default='harddisk', choices=['harddisk', 'rescue']),
				force_reboot = dict(required=False, default='no', choices=BOOLEANS),
				template = dict(required=False, default='None'),
				hostname = dict(required=False, default='None')
				),
			supports_check_mode=True
			)
	if not HAS_OVH:
		module.fail_json(msg='OVH Api wrapper not installed')
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
	elif module.params['service'] == 'list':
		objects = ['dedicated', 'templates', 'ovhtemplates', 'vrack']
		if module.params['name'] == 'dedicated':
			listDedicated(client, module)
		elif module.params['name'] == 'templates':
			listTemplates(client, module)
		else:
			module.exit_json(changed=False, msg="%s not supported for 'list' service" % module.params['name'])

# For Ansible < 2.1
# Still works on Ansible 2.2.0
from ansible.module_utils.basic import *

# For Ansible >= 2.1
# bug: doesn't work with ansible 2.2.0
#from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
	    main()
