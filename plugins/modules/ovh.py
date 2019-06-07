#!/usr/bin/env python

ANSIBLE_METADATA = {
    'metadata_version': '2.4',
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
    - Install new dedicated servers from a template (both OVH and personal ones)
    - Create a personal OVH template from a file (with h/w and s/w raid support)
    - Monitor installation status on dedicated servers
    - Add/Remove OVH Monitoring on dedicated servers
    - Add/Remove a dedicated server from a OVH vrack
    - Restart a dedicate server on debian rescue or disk
    - List dedicated servers, personal templates
    - Create a template from a yml file inside an ansible role (see README)
    - Terminate a dedicated server (doesn't confirm termination, has to be done manually)
author: Francois BRUNHES and Synthesio SRE Team
notes:
    - "In /etc/ovh.conf (on host that executes module), you should add your
      OVH API credentials like:
      [default]
      ; general configuration: default endpoint
      endpoint=ovh-eu

      [ovh-eu]
      ; configuration specific to 'ovh-eu' endpoint
      application_key=<YOUR APPLICATION KEY>
      application_secret=<YOUR APPLICATIOM SECRET>
      consumer_key=<YOUR CONSUMER KEY>

    Or you can provide these values as module's attributes."
requirements:
    - ovh >= 0.4.8
options:
    endpoint:
            required: false
            description: The API endpoint to use
    application_key:
            required: false
            description: The application key to use to connect to the API
    application_secret:
            required: false
            description: The application secret to use to connect to the API
    consumer_key:
            required: false
            description: The consumer key to use to connect to the API
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
        choices: ['boot', 'dns', 'vrack', 'reverse', 'monitoring', 'install', 'status', 'list', 'template', 'terminate']
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
              template, create/delete an ovh template from a yaml file
              terminate, give back a dedicated server to OVH
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
    link_type:
        required: false
        default: private
        description:
            - The interface type you want to detect
    max_retry:
        required: false
        default: 10
        description:
            - Number of tries for the operation to suceed. OVH api can be lazy.
    sleep:
        required: false
        default: 10
        description:
            - seconds between to tries
'''

EXAMPLES = '''
- name: Add server to vrack
  ovh:
    service: vrack
    vrack: "VRACK ID"
    name: "HOSTNAME"

- name: Add server IP to DNS
  ovh:
    service: dns
    domain: "example.com"
    ip: "192.0.21"
    name: "internal.bar"

- name: Refresh domain
  ovh:
    service: dns
    name: refresh
    domain: "example.com"

- name: Change Reverse on server
  ovh:
    service: reverse
    name: "internal.bar"
    ip: "192.0.2.1"
    domain: "example.com"

- name: Install the dedicated server
  ovh:
    service: install
    name: "ovhname.ovh.eu"
    hostname: "internal.bar.example.com"
    template: "SOME TEMPLATE"

- name: Wait until installation is finished
  local_action:
    module: ovh
    args:
      service: status
      name: "ovhname.ovh.eu"
      max_retry: 150
      sleep: 10
  ovh:
    service: monitoring
    name: "ovhname.ovh.eu"
    state: "present / absent"

- name: Get list of servers
  ovh:
    service: list
    name: dedicated
  register: servers

- name: Get list of personal templates
  ovh:
    service: list
    name: templates
  register: templates

- name: check if template is already installed
  ovh:
    service: list
    name: templates
  register: templates

- name: Create template
  ovh:
    service: template
    name: custom_template
    state: "present"
  run_once: yes
  when: template not in templates.objects

- name: Install the dedicated server
  ovh:
    service: install
    name: ovhname.ovh.eu
    hostname: "internal.bar.example.com"
    template: "custom_template"
    ssh_key_name="My Key"
    use_distrib_kernel=True

- name: Delete template
  ovh:
    service: template
    name: "custom_template"
    state: "absent"
  run_once: yes

- name: terminate server
  ovh:
    service: terminate
    name: "ns6666666.ip-42-422-42.eu"
'''

RETURN = ''' # '''

import ast
import yaml
import time

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

from ansible.module_utils.basic import AnsibleModule
from ansible.utils.display import Display
from ansible import constants as C

display = Display()

def getStatusInstall(ovhclient, module):
    if module.params['name']:
        if module.check_mode:
            module.exit_json(changed=False, msg="done - (dry run mode)")
        for i in range (1, int(module.params['max_retry'])):
            # Messages cannot be displayed in real time (yet): https://github.com/ansible/proposals/issues/92
            display.display("%i out of %i" % (i, int(module.params['max_retry'])), C.COLOR_VERBOSE)
            try:
                tasklist = ovhclient.get('/dedicated/server/%s/task' % module.params['name'], function='reinstallServer')
                result = ovhclient.get('/dedicated/server/%s/task/%s' % (module.params['name'], max(tasklist)))
            except APIError as apiError:
                module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
            message = ""
            # Get more details in installation progression
            if "done" not in result['status']:
                progress_status = ovhclient.get('/dedicated/server/%s/install/status' % module.params['name'])
                if 'message' in progress_status and progress_status['message'] == 'Server is not being installed or reinstalled at the moment':
                    message = progress_status['message']
                else:
                    for progress in progress_status['progress']:
                        if progress["status"] == "doing":
                             message = progress['comment']
                display.display("%s: %s" % (result['status'], message), C.COLOR_VERBOSE)
                time.sleep(float(module.params['sleep']))
            else:
                module.exit_json(changed=False, msg="%s: %s" % (result['status'], message))
        module.fail_json(changed=False, msg="Max wait time reached, about %i x %i seconds" % (i, int(module.params['max_retry'])))
    else:
        module.fail_json(changed=False, msg="Please provide 'ns' server name from wich installation status will be check")


def launchInstall(ovhclient, module):
    if module.params['name'] and module.params['hostname'] and module.params['template']:
        try:
            compatible_templates = ovhclient.get('/dedicated/server/%s/install/compatibleTemplates' % module.params['name'])
            compatible_templates = set([template for template_type in compatible_templates.keys() for template in compatible_templates[template_type]])
            if module.params['template'] not in compatible_templates:
                module.fail_json(changed=False, msg="%s doesn't exist in compatibles templates" % module.params['template'])
        except APIError as apiError:
            module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
        if module.check_mode:
            module.exit_json(changed=True, msg="Installation in progress on %s ! - (dry run mode)" % module.params['name'])
        details = {"details":{"language":"en","customHostname":module.params['hostname']},"templateName":module.params['template']}
        if module.params.get('ssh_key_name', None):
            try:
                result = ovhclient.get('/me/sshKey')
                if module.params['ssh_key_name'] not in result:
                    module.fail_json(changed=False, msg="%s doesn't exist in public SSH keys" % module.params['ssh_key_name'])
                else:
                    details['details']['sshKeyName'] = module.params['ssh_key_name']
            except APIError as apiError:
                module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
        if module.params.get('use_distrib_kernel', False):
                details['details']['useDistribKernel'] = module.params['use_distrib_kernel']
        try:
            ovhclient.post('/dedicated/server/%s/install/start' % module.params['name'],
                    **details)
		#TODO : check if details are still properly formed, even for a HW Raid config. For instance:  {"details":{"language":"en","customHostname":"test01.test.synthesio.net","installSqlServer":false,"postInstallationScriptLink":null,"postInstallationScriptReturn":null,"sshKeyName":"deploy","useDistribKernel":true,"useSpla":false,"softRaidDevices":null,"noRaid":false,"diskGroupId":null,"resetHwRaid":false},"templateName":"test"}
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
            shouldbe = True
        elif module.params['state'] == 'absent':
            shouldbe = False
        else:
            module.fail_json(changed=False, msg="State %s does not match 'present' or 'absent'" % module.params['state'])

        if module.check_mode:
            module.exit_json(changed=True, msg="Monitoring %s on %s - (dry run mode)" % (module.params['state'], module.params['name']))

        for i in range (1, int(module.params['max_retry'])):
            server_state = ovhclient.get('/dedicated/server/%s' % module.params['name'])

            if server_state['monitoring'] != shouldbe:
                try:
                    ovhclient.put('/dedicated/server/%s' % module.params['name'],
                        monitoring = shouldbe)
                except APIError as apiError:
                    module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
            else:
                if shouldbe:
                        module.exit_json(changed=True, msg="Monitoring activated on %s after %i time(s)" % (module.params['name'],i))
                else:
                        module.exit_json(changed=True, msg="Monitoring deactivated on %s after %i time(s)" % (module.params['name'], i))
            time.sleep(float(module.params['sleep']))
        module.fail_json(changed=False, msg="Could not change monitoring flag")
    else:
        if not module.params['name']:
            module.fail_json(changed=False, msg="Please give a name to change monitoring state")
        if not module.params['state']:
            module.fail_json(changed=False, msg="Please give a state for your monitoring")

def terminateServer(ovhclient, module):
    if module.params['name']:
        if module.check_mode:
                    module.exit_json(changed=True, msg="Terminate %s is done, please confirm via the email sent - (dry run mode)" % module.params['name'])
        try:
            ovhclient.post('/dedicated/server/%s/terminate' % module.params['name'])
            module.exit_json(changed=True, msg="Terminate %s is done, please confirm via the email sent" % module.params['name'])
        except APIError as apiError:
            module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
    else:
        module.fail_json(changed=False, msg="Please give a dedicated name to terminate")

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
                # There is no easy way to know if the server is on an old or new network generation.
                # So we need to call this new route to ask for virtualNetworkInterface, and if the answer is empty, it's on a old generation.
                # The /vrack/%s/allowedServices route used previously has availability and scaling problems.
                result = ovhclient.get('/dedicated/server/%s/virtualNetworkInterface'  % module.params['name'], mode='vrack')
            except APIError as apiError:
                module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
# XXX: In a near future, OVH will add the possibility to add multiple interfaces to the same VRACK or another one
# This code may break at this moment because each server will have a list of dedicatedServerInterface
            # New generation
            if len(result):
                try:
                    is_already_registered = ovhclient.get('/vrack/%s/dedicatedServerInterfaceDetails' % module.params['vrack'])
                except APIError as apiError:
                    module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
                for new_server in is_already_registered:
                    if new_server['dedicatedServer'] == module.params['name']:
                        module.exit_json(changed=False, msg="%s is already registered on %s" % (module.params['name'], module.params['vrack']))
                try:
                    serverInterface="".join(result)
                    result2 = ovhclient.post('/vrack/%s/dedicatedServerInterface' % module.params['vrack'],
                            dedicatedServerInterface=serverInterface)
                    module.exit_json(changed=True, contents=result2)
                except APIError as apiError:
                    module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
            # Old generation
            else:
                try:
                    is_already_registered = ovhclient.get('/vrack/%s/dedicatedServer' % module.params['vrack'])
                except APIError as apiError:
                    module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
                for old_server in is_already_registered:
                    if old_server == module.params['name']:
                        module.exit_json(changed=False, msg="%s is already registered on %s" % (module.params['name'], module.params['vrack']))
                try:
                    result2 = ovhclient.post('/vrack/%s/dedicatedServer' % module.params['vrack'],
                    dedicatedServer=module.params['name'])
                    module.exit_json(changed=True, contents=result2)
                except APIError as apiError:
                    module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
        elif module.params['state'] == 'absent':
            try:
                    result_new = ovhclient.get('/vrack/%s/dedicatedServerInterfaceDetails' % module.params['vrack'])
                    result_old = ovhclient.get('/vrack/%s/dedicatedServer' % module.params['vrack'])
            except APIError as apiError:
                    module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
            for new_server in result_new:
                if new_server['dedicatedServer'] == module.params['name']:
                    try:
                        result = ovhclient.delete('/vrack/%s/dedicatedServerInterface/%s' % (module.params['vrack'], new_server['dedicatedServerInterface']))
                        module.exit_json(changed=True, contents=result)
                    except APIError as apiError:
                        module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
            for old_server in result_old:
                if old_server == module.params['name']:
                    try:
                        result = ovhclient.delete('/vrack/%s/dedicatedServer/%s' % (module.params['vrack'], module.params['name']))
                        module.exit_json(changed=True, contents=result)
                    except APIError as apiError:
                        module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
            module.exit_json(changed=False, msg="No %s in %s" % (module.params['name'], module.params['vrack']))
        else:
            module.exit_json(changed=False, msg="Vrack service only uses present/absent state")
    else:
        module.fail_json(changed=False, msg="Please give a vrack name to add/remove your server")

def generateTemplate(ovhclient, module):
    if module.params['template']:
        if module.check_mode:
            module.exit_json(changed=True, msg="%s succesfully %s on ovh API - (dry run mode)" % (module.params['template'], module.params['state']))
        src = module.params['template']
        with open(src, 'r') as stream:
            content = yaml.load(stream)
        conf = {}
        for i,j in content.iteritems():
            conf[i] = j
        if module.params['state'] == 'present':
            try:
                result = ovhclient.post('/me/installationTemplate', baseTemplateName = conf['baseTemplateName'], defaultLanguage = conf['defaultLanguage'], name = conf['templateName'])
            except APIError as apiError:
                module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
            Templates = { 'customization': {"customHostname":conf['customHostname'],"postInstallationScriptLink":conf['postInstallationScriptLink'],"postInstallationScriptReturn":conf['postInstallationScriptReturn'],"sshKeyName":conf['sshKeyName'],"useDistributionKernel":conf['useDistributionKernel']},'defaultLanguage':conf['defaultLanguage'],'templateName':conf['templateName'] }
            try:
                result = ovhclient.put('/me/installationTemplate/%s' % conf['templateName'], **Templates)
            except APIError as apiError:
                 module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
            try:
                result = ovhclient.post('/me/installationTemplate/%s/partitionScheme' % conf['templateName'], name=conf['partitionScheme'], priority=conf['partitionSchemePriority'])
            except APIError as apiError:
                module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
            if conf['isHardwareRaid']:
                result = ovhclient.get('/dedicated/server/%s/install/hardwareRaidProfile' % module.params['name'])
                if len(result['controllers']) == 1:
                    # XXX: Only works with a server who has one controller. All the disks in this controller are taken to form one raid
                    # In the future, some of our servers could have more than one controller, so we will have to adapt this code
                    disks = result['controllers'][0]['disks'][0]['names']
                    #if 'raid 1' in conf['raidMode']:
                        #TODO : create a list of disks like this: {"disks":["[c0:d0,c0:d1]","[c0:d2,c0:d3]","[c0:d4,c0:d5]","[c0:d6,c0:d7]","[c0:d8,c0:d9]","[c0:d10,c0:d11]"],"mode":"raid10","name":"managerHardRaid","step":1}
                    #else:
			#TODO : for raid 0, it's assumed that a simple list of disks would be sufficient
                    try:
                        result = ovhclient.post('/me/installationTemplate/%s/partitionScheme/%s/hardwareRaid' % (conf['templateName'], conf['partitionScheme']),
                            disks=disks,
                            mode=conf['raidMode'],
                            name=conf['partitionScheme'],
                            step=1)
                    except APIError as apiError:
                        module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
                else:
                    module.fail_json(changed=False, msg="Failed to call OVH API: {0} Code can't handle more than one controller when using Hardware Raid setups")
            partition = {}
            for k in conf['partition']:
                partition = ast.literal_eval(k)
                try:
                    if 'raid' in partition.keys():
                        ovhclient.post('/me/installationTemplate/%s/partitionScheme/%s/partition' % (conf['templateName'], conf['partitionScheme']),
                                filesystem=partition['filesystem'],
                                mountpoint=partition['mountpoint'],
                                raid=partition['raid'],
                                size=partition['size'],
                                step=partition['step'],
                                type=partition['type'])
                    else:
                        ovhclient.post('/me/installationTemplate/%s/partitionScheme/%s/partition' % (conf['templateName'], conf['partitionScheme']),
                                filesystem=partition['filesystem'],
                                mountpoint=partition['mountpoint'],
                                size=partition['size'],
                                step=partition['step'],
                                type=partition['type'])
                except APIError as apiError:
                    module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
            try:
                ovhclient.post('/me/installationTemplate/%s/checkIntegrity' % conf['templateName'])
            except APIError as apiError:
                module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError)) 
	    module.exit_json(changed=True, msg="Template %s succesfully created" % conf['templateName'])
        elif module.params['state'] == 'absent':
            try:
                ovhclient.delete('/me/installationTemplate/%s' % conf['templateName'])
            except APIError as apiError:
                module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
            module.exit_json(changed=True, msg="Template %s succesfully deleted" % conf['templateName'])
        else:
            module.fail_json(changed=False, msg="State %s not supported. Only present/absent" % module.params['state'])
    else:
        module.fail_json(changed=False, msg="No template parameter given")

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
        except APIError as apiError:
            module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
        module.exit_json(changed=True, msg="%s is now set to boot on %s." % (module.params['name'], module.params['boot']))
    if module.params['force_reboot']:
        try:
            ovhclient.post('/dedicated/server/%s/reboot' % module.params['name'])
        except APIError as apiError:
            module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))
        module.exit_json(changed=False, msg="%s is now rebooting on %s" % (module.params['name'], module.params['boot']))
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

def getMac(ovhclient, module):
    result = ovhclient.get('/dedicated/server/%s/networkInterfaceController?linkType=%s' % (module.params['name'], module.params['link_type']))
    module.exit_json(changed=False, msg=result)

def main():
    module = AnsibleModule(
            argument_spec = dict(
                endpoint = dict(required=False, default=None),
                application_key = dict(required=False, default=None),
                application_secret = dict(required=False, default=None),
                consumer_key = dict(required=False, default=None),
                state = dict(default='present', choices=['present', 'absent', 'modified']),
                name  = dict(required=True),
                service = dict(choices=['boot', 'dns', 'vrack', 'reverse', 'monitoring', 'install', 'status', 'list', 'template', 'terminate', 'getmac'], required=True),
                domain = dict(required=False, default=None),
                ip    = dict(required=False, default=None),
                vrack = dict(required=False, default=None),
                boot = dict(default='harddisk', choices=['harddisk', 'rescue']),
                force_reboot = dict(required=False, type='bool', default=False),
                template = dict(required=False, default=None),
                hostname = dict(required=False, default=None),
                max_retry = dict(required=False, default=10),
                sleep = dict(required=False, default=10),
                ssh_key_name = dict(required=False, default=None),
                use_distrib_kernel = dict(required=False, type='bool', default=False),
                link_type =  dict(required=False, default='private', choices=['public', 'private'])
                ),
            supports_check_mode=True
            )
    if not HAS_OVH:
        module.fail_json(msg='OVH Api wrapper not installed')
    credentials = ['endpoint', 'application_key', 'application_secret', 'consumer_key']
    credentials_in_parameters = [cred in module.params for cred in credentials]
    try:
        if all(credentials_in_parameters):
            client = ovh.Client(**{credential: module.params[credential] for credential in credentials})
        else:
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
        if module.params['name'] == 'dedicated':
            listDedicated(client, module)
        elif module.params['name'] == 'templates':
            listTemplates(client, module)
        else:
            module.fail_json(changed=False, msg="%s not supported for 'list' service" % module.params['name'])
    elif module.params['service'] == 'template':
        generateTemplate(client, module)
    elif module.params['service'] == 'terminate':
        terminateServer(client, module)
    elif module.params['service'] == 'getmac':
        getMac(client, module)

if __name__ == '__main__':
        main()
