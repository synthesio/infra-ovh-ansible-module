from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError, AnsibleActionFail
from ansible.module_utils._text import to_text


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp

        resolved_template = self._task.args.get('template', None)
        try:
            # We use _find_needle to resolve the path where the template file
            # is stored in ansible role
            resolved_template = self._find_needle('files', resolved_template)
        except AnsibleError as e:
            raise AnsibleActionFail(to_text(e))

        module_return = dict(changed=False)
        # We copy the module and re-run it with the updated template path
        module_args = self._task.args.copy()
        module_args.update(
            dict(
                template=resolved_template
            )
        )
        module_return = self._execute_module(
            module_name='synthesio.ovh.installation_template',
            module_args=module_args,
            task_vars=task_vars)

        result.update(module_return)

        return result
