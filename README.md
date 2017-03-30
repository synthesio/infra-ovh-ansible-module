# An Ansible module to talk with OVH API.

## Requirements
python 2.7
pip install ovh

Works with Ansible 1.9.6 and 2.2.0

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
  until: result.msg.find("done") != -1
  retries: 150
  delay: 10
```

### Enable / disable OVH monitoring

```
- name: Remove ovh monitoring when necessary
  ovh: service='monitoring' name='foo.ovh.eu' state='present / absent'
```
