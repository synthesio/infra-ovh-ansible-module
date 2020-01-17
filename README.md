# An Ansible module to talk with OVH API.

## Requirements

- python 2.7+ or 3.5+
- python-ovh: https://github.com/ovh/python-ovh
- Only tested with Ansible 2.7+

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
    vrack: "{{ vrackid }}"
    name: "{{ ovhname }}"
```

This allows you to store them in Ansible vault or to use any lookup plugin to retrieve them.

## Usage

Here are a few examples of what you can do. Please read the module for everything else, it most probably does it!

### Add a host into the vrack

```
- name: Add server to vrack
  ovh:
    service: vrack
    vrack: "{{ vrackid }}"
    name: "{{ ovhname }}"
```

### Add a DNS entry for `internal.bar.example.com`

```
- name: Add server IP to DNS
  ovh:
    service: dns
    domain: "example.com"
    ip: "192.0.2.1"
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
    name: "{{ ovhname }}"
    hostname: "{{ inventory_hostname }}.{{ domain }}"
    template: "{{ template }}"
  
- name: Wait until installation is finished
  ovh:
    service: status
    name: "{{ ovhname }}"
    max_retry: 150
    sleep: 10
  delegate_to: localhost

```

### Enable / disable OVH monitoring

```
- name: Remove ovh monitoring when necessary
  ovh:
    service: monitoring
    name: "{{ ovhname }}"
    state: "absent"
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
    name: "{{ ovhname }}"
    hostname: "internal.bar.example.com"
    template: "custom_template"
    ssh_key_name: "My Key"
    use_distrib_kernel: True

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
    name: "{{ ovhname }}"
```

An example of yml template is in roles directory of this repository
