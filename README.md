# An Ansible module to talk with OVH API.

## Requirements

- python 2.7
- python-ovh: https://github.com/ovh/python-ovh
- Only tested with Ansible 2.7.0+

## Configuration

In your `ansible.cfg` :

```
action_plugin_path=path/to/ovh/plugins/action
module_path=path/to/ovh/plugins/modules
```

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
  ovh:
    endpoint: "ovh-eu"
    application_key: "<YOUR APPLICATION KEY>"
    application_secret: "<YOUR APPLICATIOM SECRET>"
    consumer_key: "<YOUR CONSUMER KEY>"
    service: vrack
    vrack: "VRACK ID"
    name: "HOSTNAME"
```

This allows you to store them in Ansible vault or to use any lookup plugin to retrieve them.

## Usage

Here are a few examples of what you can do. Please read the module for everything else, it most probably does it!

### Add a host into the vrack

```
- name: Add server to vrack
  ovh:
    service: vrack
    vrack: "VRACK ID"
    name: "HOSTNAME"
```

### Add a DNS entry for `internal.bar.example.com`

```
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
```

### Change a server reverse

```
- name: Change Reverse on server
  ovh:
    service: reverse
    name: "internal.bar"
    ip: "192.0.2.1"
    domain: "example.com"
```


### Install a server from a template

```
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

```

### Enable / disable OVH monitoring

```
- name: Remove ovh monitoring when necessary
  ovh:
    service: monitoring
    name: "ovhname.ovh.eu"
    state: "present / absent"
```

### List dedicated servers or personal templates
```
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
```

### Create a new template and install it
```
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

### Terminate the rent of an ovh dedicated server
- name: terminate server
  ovh:
    service: terminate
    name: "ns6666666.ip-42-422-42.eu"
```

An example of yml template is in roles directory of this repository
