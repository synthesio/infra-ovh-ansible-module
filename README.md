# An Ansible collection to talk with OVH API

## Requirements

Tested with:

- Python 3.8
- [Python-ovh 1.0](https://github.com/ovh/python-ovh)
- Ansible 2.11+

## Collection

This module can be [installed as a collection](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html#installing-a-collection-from-a-git-repository)

```shell
ansible-galaxy collection install git+https://github.com/synthesio/infra-ovh-ansible-module
```

This collection provides the following modules:

```text
dedicated_server_boot
dedicated_server_display_name
dedicated_server_info
dedicated_server_install
dedicated_server_install_wait
dedicated_server_monitoring
dedicated_server_networkinterfacecontroller
dedicated_server_terminate
dedicated_server_vrack
domain
installation_template
ip_reverse
public_cloud_flavorid_info
public_cloud_imageid_info
public_cloud_instance_info
public_cloud_instance
public_cloud_instance_delete
public_cloud_monthly_billing
public_cloud_block_storage_instance
public_cloud_block_storage
public_cloud_object_storage
public_cloud_object_storage_policy
```

You can read the documentation of every modules with `ansible-doc synthesio.ovh.$modules`

An example for a custom template to install a dedicated server is present in `roles/ovhtemplate` folder

## Configuration

The collection path must be defined in your `ansible.cfg` :

```ini
[defaults]
collections_paths = collections/
```

In `/etc/ovh.conf`:

```ini
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

```yaml
- name: Add server to vrack
  synthesio.ovh.dedicated_server_vrack:
    endpoint: "ovh-eu"
    application_key: "<YOUR APPLICATION KEY>"
    application_secret: "<YOUR APPLICATIOM SECRET>"
    consumer_key: "<YOUR CONSUMER KEY>"
    vrack: "{{ vrackid }}"
    service_name: "{{ ovhname }}"
```

This allows you to store them in Ansible vault or to use any lookup plugin to retrieve them.

## Usage

Here are a few examples of what you can do. Please read the module for everything else, it most probably does it!

As this is a collection now you must declare it in each task.

A few examples:

### Add a host into the vrack

```yaml
- name: Add server to vrack
  synthesio.ovh.dedicated_server_vrack:
    service_name: "{{ ovhname }}"
    vrack: "{{ vrackid }}"
```

### Add a DNS entry for `internal.bar.example.com`

```yaml
- name: Add server IP to DNS
  synthesio.ovh.domain:
    domain: "example.com"
    value: "192.0.2.1"
    record_type: "A"
    name: "internal.bar"
    record_ttl: 10

```

### Install a new dedicated server

```yaml
- Install new dedicated server
  synthesio.ovh.dedicated_server_install:
    service_name: "ns12345.ip-1-2-3.eu"
    hostname: "server01.example.net"
    template: "debian10_64"

- name: Wait for the server installation
  synthesio.ovh.dedicated_server_install_wait:
    service_name: "ns12345.ip-1-2-3.eu"
    max_retry: "240"
    sleep: "10"
```

### Install a new dedicated server with only 2 disks

```yaml
- Install new dedicated server
  synthesio.ovh.dedicated_server_install:
    service_name: "ns12345.ip-1-2-3.eu"
    hostname: "server01.example.net"
    template: "debian10_64"
    soft_raid_devices: "2"

```

### Install a public cloud instance

```yaml
- name: run a public cloud installation
  synthesio.ovh.public_cloud_instance:
    name: "{{ inventory_hostname }}"
    ssh_key_id: "{{ ssh_key_id }}"
    service_name: "{{ service_name }}"
    networks: "{{ networks }}"
    flavor_id: "{{ flavor_id }}"
    region: "{{ region }}"
    image_id: "{{ image_id }}"
```
