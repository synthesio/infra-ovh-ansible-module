#!/usr/bin/env python

import ast
import yaml
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.utils.display import Display
from ansible import constants

try:
    import ovh
    from ovh.exceptions import APIError, ResourceNotFoundError

    HAS_OVH = True
except ImportError:
    HAS_OVH = False


ANSIBLE_METADATA = {
    "metadata_version": "3.0",
    "supported_by": "community",
    "status": ["preview"],
}

DOCUMENTATION = """
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
        choices: ['boot', 'dns', 'vrack', 'reverse', 'monitoring', 'install', 'status',
                  'list', 'template', 'terminate']
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
    record_type:
        required: false
        default: 'A'
        description:
            - The kind of DNS record to create/modify/delete
    txt:
        required: false
        default: None
        description:
            - The value of the DNS TXT record to create/modify/delete
    value:
        required: false
        default: None
        description:
            - The value of the DNS record to create/modify/delete
    create:
        required: false
        default: None
        description:
            - If the DNS entry must created when it does not exist and state id 'modified'
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
"""

EXAMPLES = """
- name: Add server to vrack
  ovh:
    service: vrack
    vrack: "VRACK ID"
    name: "HOSTNAME"

- name: Add a DNS (TXT) entry for `_acme-challenge.site.example.com`
  ovh:
    service: 'dns'
    domain: 'example.com'
    name: '_acme-challenge.site'
    txt: 'd41d8cd98f00b204e9800998ecf8427e'

- name: Add a DNS (A) entry for `internal.bar.foo.com`
  ovh:
    service: dns
    domain: "example.com"
    ip: "192.0.21"
    name: "internal.bar"

- name: Add a DNS (CNAME) entry for `internal.bar.foo.com` that will an CNAME for `external.com`
  ovh:
    service: dns
    domain: "example.com"
    record_type: "CNAME"
    value: "external.com."
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
"""

RETURN = """ # """

display = Display()


def main():
    argument_spec = dict(
        endpoint=dict(required=False, default=None),
        application_key=dict(required=False, default=None),
        application_secret=dict(required=False, default=None),
        consumer_key=dict(required=False, default=None),
        state=dict(default="present", choices=["present", "absent", "modified"]),
        name=dict(required=True),
        service=dict(
            choices=[
                "boot",
                "dns",
                "vrack",
                "reverse",
                "monitoring",
                "install",
                "status",
                "list",
                "template",
                "terminate",
                "getmac",
            ],
            required=True,
        ),
        domain=dict(required=False, default=None),
        ip=dict(required=False, default=None),
        record_type=dict(required=False, default=u"A"),
        value=dict(required=False, default=None),
        txt=dict(required=False, default=None),
        create=dict(required=False, type="bool", default=False),
        vrack=dict(required=False, default=None),
        boot=dict(default="harddisk", choices=["harddisk", "rescue"]),
        force_reboot=dict(required=False, type="bool", default=False),
        template=dict(required=False, default=None),
        hostname=dict(required=False, default=None),
        max_retry=dict(required=False, default=10),
        sleep=dict(required=False, default=10),
        ssh_key_name=dict(required=False, default=None),
        use_distrib_kernel=dict(required=False, type="bool", default=False),
        link_type=dict(
            required=False, default="private", choices=["public", "private"]
        ),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    om = OVHModule(module, module.check_mode, module.params)
    error, changed, result = om.run()
    if error is None:
        module.exit_json(changed=changed, **result)
    else:
        module.fail_json(msg=error, **result)


class OVHModule:
    def __init__(self, module, check_mode, params):
        self.module = module
        self.check_mode = check_mode
        self.params = params
        self.client = None

    def run(self):
        """Return error, changed, result"""
        if not HAS_OVH:
            return self.fail("OVH Api wrapper not installed")

        credentials = [
            "endpoint",
            "application_key",
            "application_secret",
            "consumer_key",
        ]
        credentials_in_parameters = [cred in self.params for cred in credentials]
        try:
            if all(credentials_in_parameters):
                self.client = ovh.Client(
                    **{
                        credential: self.params[credential]
                        for credential in credentials
                    }
                )
            else:
                self.client = ovh.Client()
        except APIError as api_error:
            return self.fail("Failed to call OVH API: {0}".format(api_error))

        choice_map = dict(
            dns=self.change_dns,
            getmac=self.get_mac,
            terminate=self.terminate_server,
            status=self.get_status_install,
            install=self.launch_install,
            monitoring=self.change_monitoring,
            reverse=self.change_reverse,
            list=self.list_service,
            boot=self.change_boot_dedicated,
            template=self.generate_template,
            vrack=self.change_vrack,
        )

        return choice_map.get(self.params["service"])()

    def fail(self, message):
        return message, False, {}

    def succeed(self, message, changed=True, contents=None, objects=None):
        result = {}
        if message is not None:
            result["msg"] = message
        if contents is not None:
            result["contents"] = contents
        if objects is not None:
            result["objects"] = objects

        return None, changed, result

    def change_dns(self):
        domain = self.params["domain"]
        ip = self.params["ip"]
        record_type = self.params["record_type"]
        value = self.params["value"]
        txt = self.params["txt"]
        name = self.params["name"]
        state = self.params["state"]
        create = self.params["create"]

        msg = ""

        if not domain:
            return self.fail("Please give a domain to add your target")

        if not name:
            return self.fail("Please give a name for your entry")

        if name == "refresh" and not ip and not txt and not value:
            if self.check_mode:
                return self.succeed(
                    "Domain %s succesfully refreshed ! - (dry run mode)" % domain,
                    changed=True,
                )

            try:
                self.client.post("/domain/zone/%s/refresh" % domain)
                return self.succeed(
                    "Domain %s succesfully refreshed !" % domain, changed=True
                )
            except APIError as api_error:
                return self.fail("Failed to call OVH API: {0}".format(api_error))

        if self.check_mode:
            return self.succeed(
                "DNS succesfully %s on %s - (dry run mode)" % (state, name),
                changed=True,
            )

        if ip:
            if record_type != "A":
                return self.fail(
                    "Inconsistent data in task, should provide a record_type != 'A' "
                    "if IP is provided"
                )
            elif txt or value:
                return self.fail(
                    "Inconsistent data in task, should not provide TXT or VALUE if IP is provided"
                )
            else:
                record_type = "A"
                value = ip
        elif txt:
            record_type = "TXT"
            value = txt
        elif value and record_type:
            record_type = record_type.upper()
        else:
            return self.fail("Please give an IP to add your target")

        try:
            check = self.client.get(
                "/domain/zone/%s/record" % domain, fieldType=record_type, subDomain=name
            )
        except APIError as api_error:
            return self.fail("Failed to call OVH API: {0}".format(api_error))

        if state == "present":
            if check:
                return self.succeed(
                    "%s is already registered in domain %s" % (name, domain),
                    changed=False,
                )

            try:
                result = self.client.post(
                    "/domain/zone/%s/record" % domain,
                    fieldType=record_type,
                    subDomain=name,
                    target=value,
                )
                return self.succeed(message=None, contents=result, changed=True)
            except APIError as api_error:
                return self.fail("Failed to call OVH API: {0}".format(api_error))

        elif state == "modified":
            if not check:
                if not create:
                    return self.fail(
                        "The target %s doesn't exist in domain %s" % (name, domain)
                    )
                else:
                    try:
                        result = self.client.post(
                            "/domain/zone/%s/record" % domain,
                            fieldType=record_type,
                            subDomain=name,
                            target=value,
                        )
                        return self.succeed(message=None, contents=result, changed=True)
                    except APIError as api_error:
                        return self.fail(
                            "Failed to call OVH API: {0}".format(api_error)
                        )

            try:
                for ind in check:
                    self.client.put(
                        "/domain/zone/%s/record/%s" % (domain, ind),
                        subDomain=name,
                        target=value,
                    )
                    msg += (
                        '{ "fieldType": "%s", "id": "%s", "subDomain": "%s",'
                        '"target": "%s", "zone": "%s" } '
                        % (record_type, ind, name, value, domain)
                    )
                return self.succeed(msg, changed=True)
            except APIError as api_error:
                return self.fail("Failed to call OVH API: {0}".format(api_error))

        elif state == "absent":
            if not check:
                return self.succeed(
                    "Target %s doesn't exist on domain %s" % (name, domain),
                    changed=False,
                )

            try:
                for ind in check:
                    self.client.delete("/domain/zone/%s/record/%s" % (domain, ind))
                return self.succeed(
                    "Target %s succesfully deleted from domain %s" % (name, domain),
                    changed=True,
                )
            except APIError as api_error:
                return self.fail("Failed to call OVH API: {0}".format(api_error))

    def get_mac(self):
        name = self.params["name"]
        link_type = self.params["link_type"]
        result = self.client.get(
            "/dedicated/server/%s/networkInterfaceController?linkType=%s"
            % (name, link_type)
        )
        return self.succeed(result, changed=False)

    def terminate_server(self):
        name = self.params["name"]

        if not name:
            return self.fail("Please give a dedicated name to terminate")

        if self.check_mode:
            return self.succeed(
                "Terminate %s is done, please confirm via the email sent - (dry run mode)"
                % name,
                changed=True,
            )

        try:
            self.client.post("/dedicated/server/%s/terminate" % name)
            return self.succeed(
                "Terminate %s is done, please confirm via the email sent" % name,
                changed=True,
            )
        except APIError as api_error:
            return self.fail("Failed to call OVH API: {0}".format(api_error))

    def get_status_install(self):
        name = self.params["name"]
        max_retry = self.params["max_retry"]
        sleep = self.params["sleep"]

        if not name:
            return self.fail(
                "Please provide 'ns' server name from which installation status will be check"
            )

        if self.check_mode:
            return self.succeed("done - (dry run mode)", changed=False)

        for i in range(1, int(max_retry)):
            # Messages cannot be displayed in real time (yet):
            #   https://github.com/ansible/proposals/issues/92
            display.display(
                "%i out of %i" % (i, int(max_retry)), constants.COLOR_VERBOSE
            )
            try:
                tasklist = self.client.get(
                    "/dedicated/server/%s/task" % name, function="reinstallServer"
                )
                result = self.client.get(
                    "/dedicated/server/%s/task/%s" % (name, max(tasklist))
                )
            except APIError as api_error:
                return self.fail("Failed to call OVH API: {0}".format(api_error))

            message = ""
            # Get more details in installation progression
            if "done" in result["status"]:
                return self.succeed(
                    "%s: %s" % (result["status"], message), changed=False
                )

            progress_status = self.client.get(
                "/dedicated/server/%s/install/status" % name
            )
            if (
                "message" in progress_status
                and progress_status["message"]
                == "Server is not being installed or reinstalled at the moment"
            ):
                message = progress_status["message"]
            else:
                for progress in progress_status["progress"]:
                    if progress["status"] == "doing":
                        message = progress["comment"]
            display.display(
                "%s: %s" % (result["status"], message), constants.COLOR_VERBOSE
            )
            time.sleep(float(sleep))
        return self.fail(
            "Max wait time reached, about %i x %i seconds" % (i, int(max_retry))
        )

    def launch_install(self):
        name = self.params["name"]
        template = self.params["template"]
        hostname = self.params["hostname"]
        ssh_key_name = self.params.get("ssh_key_name")
        use_distrib_kernel = self.params.get("use_distrib_kernel", False)

        if not name:
            return self.fail("Please give the service's name you want to install")
        if not template:
            return self.fail("Please give a template to install")
        if not hostname:
            return self.fail("Please give a hostname for your installation")

        try:
            compatible_templates = self.client.get(
                "/dedicated/server/%s/install/compatibleTemplates" % name
            )
            compatible_templates = set(
                [
                    tpl
                    for template_type in compatible_templates.keys()
                    for tpl in compatible_templates[template_type]
                ]
            )
            if template not in compatible_templates:
                return self.fail("%s doesn't exist in compatibles templates" % template)
        except APIError as api_error:
            return self.fail("Failed to call OVH API: {0}".format(api_error))

        if self.check_mode:
            return self.succeed(
                "Installation in progress on %s ! - (dry run mode)" % name, changed=True
            )

        details = {
            "details": {"language": "en", "customHostname": hostname},
            "templateName": template,
        }
        if ssh_key_name:
            try:
                result = self.client.get("/me/sshKey")
                if ssh_key_name not in result:
                    return self.fail(
                        "%s doesn't exist in public SSH keys" % ssh_key_name
                    )
                else:
                    details["details"]["sshKeyName"] = ssh_key_name
            except APIError as api_error:
                return self.fail("Failed to call OVH API: {0}".format(api_error))
        if use_distrib_kernel:
            details["details"]["useDistribKernel"] = use_distrib_kernel
        try:
            self.client.post("/dedicated/server/%s/install/start" % name, **details)
            # TODO
            # check if details are still properly formed, even for a HW Raid config.
            # For instance:
            # {'details': {'customHostname': 'test01.test.synthesio.net',
            #              'diskGroupId': None,
            #              'installSqlServer': False,
            #              'language': 'en',
            #              'noRaid': False,
            #              'postInstallationScriptLink': None,
            #              'postInstallationScriptReturn': None,
            #              'resetHwRaid': False,
            #              'softRaidDevices': None,
            #              'sshKeyName': 'deploy',
            #              'useDistribKernel': True,
            #              'useSpla': False},
            #  'templateName': 'test'}
            return self.succeed("Installation in progress on %s !" % name, changed=True)
        except APIError as api_error:
            return self.fail("Failed to call OVH API: {0}".format(api_error))

    def change_monitoring(self):
        name = self.params["name"]
        state = self.params["state"]
        max_retry = self.params["max_retry"]
        sleep = self.params["sleep"]

        if not name:
            return self.fail("Please give a name to change monitoring state")
        if not state:
            return self.fail("Please give a state for your monitoring")

        if state == "present":
            shouldbe = True
        elif state == "absent":
            shouldbe = False
        else:
            return self.fail("State %s does not match 'present' or 'absent'" % state)

        if self.check_mode:
            return self.succeed(
                "Monitoring %s on %s - (dry run mode)" % (state, name), changed=True
            )

        for i in range(1, int(max_retry)):
            server_state = self.client.get("/dedicated/server/%s" % name)

            if server_state["monitoring"] == shouldbe:
                if shouldbe:
                    return self.succeed(
                        "Monitoring activated on %s after %i time(s)" % (name, i),
                        changed=True,
                    )
                else:
                    return self.succeed(
                        "Monitoring deactivated on %s after %i time(s)" % (name, i),
                        changed=True,
                    )

            try:
                self.client.put("/dedicated/server/%s" % name, monitoring=shouldbe)
            except APIError as api_error:
                return self.fail("Failed to call OVH API: {0}".format(api_error))
            time.sleep(float(sleep))
        return self.fail("Could not change monitoring flag")

    def change_reverse(self):
        name = self.params["name"]
        domain = self.params["domain"]
        ip = self.params["ip"]

        if not domain:
            return self.fail("Please give a domain to add your target")
        if not ip:
            return self.fail("Please give an IP to add your target")

        fqdn = name + "." + domain + "."
        result = {}
        try:
            result = self.client.get("/ip/%s/reverse/%s" % (ip, ip))
        except ResourceNotFoundError:
            result["reverse"] = ""

        if result["reverse"] == fqdn:
            return self.succeed("Reverse already set", changed=False)

        if self.check_mode:
            return self.succeed(
                "Reverse %s to %s succesfully set ! - (dry run mode)" % (ip, fqdn),
                changed=True,
            )
        try:
            self.client.post("/ip/%s/reverse" % ip, ipReverse=ip, reverse=fqdn)
            return self.succeed(
                "Reverse %s to %s succesfully set !" % (ip, fqdn), changed=True
            )
        except APIError as api_error:
            return self.fail("Failed to call OVH API: {0}".format(api_error))

    def list_service(self):
        name = self.params["name"]

        if name == "dedicated":
            return self.list_dedicated()
        elif name == "templates":
            return self.list_templates()
        else:
            return self.fail("%s not supported for 'list' service" % name)

    def list_dedicated(self):
        customlist = []
        try:
            result = self.client.get("/dedicated/server")
        except APIError as api_error:
            return self.fail("Failed to call OVH API: {0}".format(api_error))

        try:
            for i in result:
                test = self.client.get("/dedicated/server/%s" % i)
                customlist.append("%s=%s" % (test["reverse"], i))
        except APIError as api_error:
            return self.fail("Failed to call OVH API: {0}".format(api_error))

        return self.succeed(message=None, changed=False, objects=customlist)

    def list_templates(self):
        customlist = []
        try:
            result = self.client.get("/me/installationTemplate")
        except APIError as api_error:
            return self.fail("Failed to call OVH API: {0}".format(api_error))

        try:
            for i in result:
                if "tmp-mgr" not in i:
                    customlist.append(i)
        except APIError as api_error:
            return self.fail("Failed to call OVH API: {0}".format(api_error))

        return self.succeed(message=None, changed=False, objects=customlist)

    def change_boot_dedicated(self):
        name = self.params["name"]
        boot = self.params["boot"]
        force_reboot = self.params["force_reboot"]

        bootid = {"harddisk": 1, "rescue": 1122}
        if self.check_mode:
            return self.succeed(
                "%s is now set to boot on %s. Reboot in progress... - (dry run mode)"
                % (name, boot),
                changed=True,
            )

        try:
            check = self.client.get("/dedicated/server/%s" % name)
        except APIError as api_error:
            return self.fail("Failed to call OVH API: {0}".format(api_error))

        if bootid[boot] != check["bootId"]:
            try:
                self.client.put("/dedicated/server/%s" % name, bootId=bootid[boot])
            except APIError as api_error:
                return self.fail("Failed to call OVH API: {0}".format(api_error))
            return self.succeed(
                "%s is now set to boot on %s." % (name, boot), changed=True
            )

        if force_reboot:
            try:
                self.client.post("/dedicated/server/%s/reboot" % name)
            except APIError as api_error:
                return self.fail("Failed to call OVH API: {0}".format(api_error))
            return self.succeed("%s is now rebooting on %s" % (name, boot))

        return self.succeed(
            "%s already configured for boot on %s" % (name, boot), changed=False
        )

    def generate_template(self):
        name = self.params["name"]
        template = self.params["template"]
        state = self.params["state"]

        if not template:
            return self.fail("No template parameter given")

        if self.check_mode:
            return self.succeed(
                "%s succesfully %s on ovh API - (dry run mode)" % (template, state),
                changed=True,
            )

        if state not in ["present", "absent"]:
            return self.fail("State %s not supported. Only present/absent" % state)

        src = template
        with open(src, "r") as stream:
            content = yaml.load(stream)
        conf = {}
        for i, j in content.iteritems():
            conf[i] = j

        if state == "absent":
            try:
                self.client.delete("/me/installationTemplate/%s" % conf["templateName"])
            except APIError as api_error:
                return self.fail("Failed to call OVH API: {0}".format(api_error))
            return self.succeed(
                "Template %s succesfully deleted" % conf["templateName"], changed=True
            )

        # state == 'present'
        try:
            result = self.client.post(
                "/me/installationTemplate",
                baseTemplateName=conf["baseTemplateName"],
                defaultLanguage=conf["defaultLanguage"],
                name=conf["templateName"],
            )
        except APIError as api_error:
            return self.fail("Failed to call OVH API: {0}".format(api_error))

        templates = {
            "customization": {
                "customHostname": conf["customHostname"],
                "postInstallationScriptLink": conf["postInstallationScriptLink"],
                "postInstallationScriptReturn": conf["postInstallationScriptReturn"],
                "sshKeyName": conf["sshKeyName"],
                "useDistributionKernel": conf["useDistributionKernel"],
            },
            "defaultLanguage": conf["defaultLanguage"],
            "templateName": conf["templateName"],
        }
        try:
            result = self.client.put(
                "/me/installationTemplate/%s" % conf["templateName"], **templates
            )
        except APIError as api_error:
            return self.fail("Failed to call OVH API: {0}".format(api_error))

        try:
            result = self.client.post(
                "/me/installationTemplate/%s/partitionScheme" % conf["templateName"],
                name=conf["partitionScheme"],
                priority=conf["partitionSchemePriority"],
            )
        except APIError as api_error:
            return self.fail("Failed to call OVH API: {0}".format(api_error))

        if conf["isHardwareRaid"]:
            result = self.client.get(
                "/dedicated/server/%s/install/hardwareRaidProfile" % name
            )

            if len(result["controllers"]) != 1:
                return self.fail(
                    "Failed to call OVH API: {0} Code can't handle more than one controller when "
                    "using Hardware Raid setups"
                )

            # XXX: Only works with a server who has one controller.
            # All the disks in this controller are taken to form one raid
            # In the future, some of our servers could have more than one controller
            # so we will have to adapt this code
            disks = result["controllers"][0]["disks"][0]["names"]

            # if 'raid 1' in conf['raidMode']:
            # TODO : create a list of disks like this
            # {'disks': ['[c0:d0,c0:d1]',
            #            '[c0:d2,c0:d3]',
            #            '[c0:d4,c0:d5]',
            #            '[c0:d6,c0:d7]',
            #            '[c0:d8,c0:d9]',
            #            '[c0:d10,c0:d11]'],
            #  'mode': 'raid10',
            #  'name': 'managerHardRaid',
            #  'step': 1}
            # else:
            # TODO : for raid 0, it's assumed that a simple list of disks would be sufficient
            try:
                result = self.client.post(
                    "/me/installationTemplate/%s/partitionScheme/%s/hardwareRaid"
                    % (conf["templateName"], conf["partitionScheme"]),
                    disks=disks,
                    mode=conf["raidMode"],
                    name=conf["partitionScheme"],
                    step=1,
                )
            except APIError as api_error:
                return self.fail("Failed to call OVH API: {0}".format(api_error))

        partition = {}
        for k in conf["partition"]:
            partition = ast.literal_eval(k)
            try:
                if "raid" in partition.keys():
                    self.client.post(
                        "/me/installationTemplate/%s/partitionScheme/%s/partition"
                        % (conf["templateName"], conf["partitionScheme"]),
                        filesystem=partition["filesystem"],
                        mountpoint=partition["mountpoint"],
                        raid=partition["raid"],
                        size=partition["size"],
                        step=partition["step"],
                        type=partition["type"],
                    )
                else:
                    self.client.post(
                        "/me/installationTemplate/%s/partitionScheme/%s/partition"
                        % (conf["templateName"], conf["partitionScheme"]),
                        filesystem=partition["filesystem"],
                        mountpoint=partition["mountpoint"],
                        size=partition["size"],
                        step=partition["step"],
                        type=partition["type"],
                    )
            except APIError as api_error:
                return self.fail("Failed to call OVH API: {0}".format(api_error))
        try:
            self.client.post(
                "/me/installationTemplate/%s/checkIntegrity" % conf["templateName"]
            )
        except APIError as api_error:
            return self.fail("Failed to call OVH API: {0}".format(api_error))

        return self.succeed(
            "Template %s succesfully created" % conf["templateName"], changed=True
        )

    def change_vrack(self):
        name = self.params["name"]
        state = self.params["state"]
        vrack = self.params["vrack"]

        if not vrack:
            return self.fail("Please give a vrack name to add/remove your server")

        if state not in ["present", "absent"]:
            return self.succeed(
                "Vrack service only uses present/absent state", changed=False
            )

        if self.check_mode:
            return self.succeed(
                "%s succesfully %s on %s - (dry run mode)" % (name, state, vrack),
                changed=True,
            )

        if state == "present":
            try:
                # There is no easy way to know if the server is on an old or new network generation.
                # So we need to call this new route to ask for virtualNetworkInterface
                # and if the answer is empty, it's on a old generation.
                # The /vrack/%s/allowedServices route used previously has availability and scaling
                # problems.
                result = self.client.get(
                    "/dedicated/server/%s/virtualNetworkInterface" % name, mode="vrack"
                )
            except APIError as api_error:
                return self.fail("Failed to call OVH API: {0}".format(api_error))

            # XXX: In a near future, OVH will add the possibility to add multiple interfaces to the
            # same VRACK or another one
            # This code may break at this moment because each server will have a list of
            # dedicatedServerInterface

            # New generation
            if len(result):
                try:
                    is_already_registered = self.client.get(
                        "/vrack/%s/dedicatedServerInterfaceDetails" % vrack
                    )
                except APIError as api_error:
                    return self.fail("Failed to call OVH API: {0}".format(api_error))

                for new_server in is_already_registered:
                    if new_server["dedicatedServer"] == name:
                        return self.succeed(
                            "%s is already registered on %s" % (name, vrack),
                            changed=False,
                        )
                try:
                    server_interface = "".join(result)
                    result2 = self.client.post(
                        "/vrack/%s/dedicatedServerInterface" % vrack,
                        dedicatedServerInterface=server_interface,
                    )
                    return self.succeed(None, contents=result2, changed=True)
                except APIError as api_error:
                    return self.fail("Failed to call OVH API: {0}".format(api_error))
            # Old generation
            else:
                try:
                    is_already_registered = self.client.get(
                        "/vrack/%s/dedicatedServer" % vrack
                    )
                except APIError as api_error:
                    return self.fail("Failed to call OVH API: {0}".format(api_error))

                for old_server in is_already_registered:
                    if old_server == name:
                        return self.succeed(
                            "%s is already registered on %s" % (name, vrack),
                            changed=False,
                        )

                try:
                    result2 = self.client.post(
                        "/vrack/%s/dedicatedServer" % vrack, dedicatedServer=name
                    )
                    return self.succeed(None, contents=result2, changed=True)
                except APIError as api_error:
                    return self.fail("Failed to call OVH API: {0}".format(api_error))

        elif state == "absent":
            try:
                result_new = self.client.get(
                    "/vrack/%s/dedicatedServerInterfaceDetails" % vrack
                )
                result_old = self.client.get("/vrack/%s/dedicatedServer" % vrack)
            except APIError as api_error:
                return self.fail("Failed to call OVH API: {0}".format(api_error))

            for new_server in result_new:
                if new_server["dedicatedServer"] == name:
                    try:
                        result = self.client.delete(
                            "/vrack/%s/dedicatedServerInterface/%s"
                            % (vrack, new_server["dedicatedServerInterface"])
                        )
                        return self.succeed(None, contents=result, changed=True)
                    except APIError as api_error:
                        return self.fail(
                            "Failed to call OVH API: {0}".format(api_error)
                        )

            for old_server in result_old:
                if old_server == name:
                    try:
                        result = self.client.delete(
                            "/vrack/%s/dedicatedServer/%s" % (vrack, name)
                        )
                        return self.succeed(None, contents=result, changed=True)
                    except APIError as api_error:
                        return self.fail(
                            "Failed to call OVH API: {0}".format(api_error)
                        )

            return self.succeed("No %s in %s" % (name, vrack), changed=False)


if __name__ == "__main__":
    main()
