# An Ansible module to talk with OVH API.

## Requirements
python 2.7
pip install ovh

Works with Ansible 1.9.6 and 2.2.0
By default, the module works with Ansible 2.2. If you want to use it with Ansible 1.9, just change at the bottom of ovh.py :
```
# For Ansible < 2.1
#from ansible.module_utils.basic import *

# For Ansible >= 2.1
# XXX: this line doesn't work with ansible 2.2.0, use the one below instead
from module_utils.basic import AnsibleModule
```

## Configuration

In `/etc/ovh.conf`:

```
[default]
; general configuration: default endpoint
endpoint=ovh-eu

[ovh-eu]
; configuration specific to 'ovh-eu' endpoint
application_key=<YOUR APPLICATION KEY>
application_secret=<YOUR APPLICATIOM SECRET>
consumer_key=<YOUR CONSUMER KEY>
```

Alternatively, you can provide credentials as module attributes:

```
- name: Add server to vrack
  ovh: endpoint='ovh-eu' application_key='<YOUR APPLICATION KEY>' application_secret='<YOUR APPLICATIOM SECRET>' consumer_key='<YOUR CONSUMER KEY>' service='vrack' vrack='VRACK ID' name='HOSTNAME'
```

This allows you to store them in Ansible vault or to use any lookup plugin to retrieve them.

## Usage

Here are a few examples of what you can do. Please read the module for everything else, it most probably does it!

### Add a host into the vrack

```
- name: Add server to vrack
  ovh: service='vrack' vrack='VRACK ID' name='HOSTNAME'
```

### Add a DNS entry for `internal.bar.foo.com`

```
- name: Add server IP to DNS
  ovh: service='dns' domain='foo.com' ip='1.2.3.4' name='internal.bar'

- name: Refresh domain
  ovh: service='dns' name='refresh' domain='{{ domain }}'
```

### Change a server reverse

```
- name: Change Reverse on server
  ovh: service=reverse name='internal.bar' ip='1.2.3.4' domain='foo.com' 
```


### Install a server from a template

```
- name: Install the dedicated server
  ovh: service='install' name='foo.ovh.eu' hostname='internal.bar.foo.com' template='SOME TEMPLATE'

- name: Wait until installation is finished
  local_action:
    module: ovh
    service: status
    name: 'foo.ovh.eu'
  register: result
  until: result.msg.find("Installation successful.") != -1
  retries: 150
  delay: 10
```

### Enable / disable OVH monitoring

```
- name: Remove ovh monitoring when necessary
  ovh: service='monitoring' name='foo.ovh.eu' state='present / absent'
```

### List dedicated servers or personal templates
```
- name: Get list of servers
  ovh: service='list' name='dedicated'
  register: servers

- name: Get list of personal templates
  ovh: service='list' name='templates'
  register: templates
```

### Create a new template and install it
```
- name: check if template is already installed
  ovh: service='list' name='templates'
  register: templates

- name: Create template
  ovh: service='template' name='custom' state='present'
  run_once: yes
  when: template not in templates.objects

- name: Install the dedicated server
  ovh: service='install' name='foo.ovh.eu' hostname='internal.bar.foo.com' template='custom' ssh_key_name='My Key' use_distrib_kernel=True
  
- name: Delete template
  ovh: service='template' name='{{ template }}' state='absent'
  run_once: yes

### Terminate the rent of an ovh dedicated server
- name: terminate server
  ovh: service=terminate name= "ns6666666.ip-42-422-42.eu"
```
An example of yml template is in roles directory of this repository
