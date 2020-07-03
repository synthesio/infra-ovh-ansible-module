# An Ansible module to talk with OVH API.

## Requirements

Only tested with:

- Python 3.7
- Python-ovh 0.5: https://github.com/ovh/python-ovh
- Ansible 2.9

## Collection

This repository must be a submodule of ansible:
```
git submodule add -f https://github.com/synthesio/infra-ovh-ansible-module collections/ansible_collections/synthesio/ovh
```

## Configuration

The collection path must be defined in your `ansible.cfg` :

```
[defaults]
collections_paths = collections/
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

As this is a collection now you must declare it in each task.

### Add a host into the vrack

```
- name: Add server to vrack
  collections:
  - synthesio.ovh
  ovh:
    service: vrack
    vrack: "{{ vrackid }}"
    name: "{{ ovhname }}"
```

### Add a DNS entry for `internal.bar.example.com`

```
- name: Add server IP to DNS
  collections:
  - synthesio.ovh
  ovh:
    service: dns
    domain: "example.com"
    ip: "192.0.2.1"
    name: "internal.bar"

- name: Refresh domain
  collections:
  - synthesio.ovh
  ovh:
    service: dns
    name: refresh
    domain: "example.com"
```

### Change a server reverse

```
- name: Change Reverse on server
  collections:
  - synthesio.ovh
  ovh:
    service: reverse
    name: "internal.bar"
    ip: "192.0.2.1"
    domain: "example.com"
```


### Install a server from a template

```
- name: Install the dedicated server
  collections:
  - synthesio.ovh
  ovh:
    service: install
    name: "{{ ovhname }}"
    hostname: "{{ inventory_hostname }}.{{ domain }}"
    template: "{{ template }}"
  
- name: Wait until installation is finished
  collections:
  - synthesio.ovh
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
  collections:
  - synthesio.ovh
  ovh:
    service: monitoring
    name: "{{ ovhname }}"
    state: "absent"
```

### List dedicated servers or personal templates
```
- name: Get list of servers
  collections:
  - synthesio.ovh
  ovh:
    service: list
    name: dedicated
  register: servers

- name: Get list of personal templates
  collections:
  - synthesio.ovh
  ovh:
    service: list
    name: templates
  register: templates
```

### Create a new template and install it
```
- name: check if template is already installed
  collections:
  - synthesio.ovh
  ovh:
    service: list
    name: templates
  register: templates

- name: Create template
  collections:
  - synthesio.ovh
  ovh:
    service: template
    name: custom_template
    state: "present"
  run_once: yes
  when: template not in templates.objects

- name: Install the dedicated server
  collections:
  - synthesio.ovh
  ovh:
    service: install
    name: "{{ ovhname }}"
    hostname: "internal.bar.example.com"
    template: "custom_template"
    ssh_key_name: "My Key"
    use_distrib_kernel: True

- name: Delete template
  collections:
  - synthesio.ovh
  ovh:
    service: template
    name: "custom_template"
    state: "absent"
  run_once: yes

### Terminate the rent of an ovh dedicated server
- name: terminate server
  collections:
  - synthesio.ovh
  ovh:
    service: terminate
    name: "{{ ovhname }}"
```

An example of yml template is in roles directory of this repository
