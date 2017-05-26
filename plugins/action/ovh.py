from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.errors import AnsibleError, AnsibleFileNotFound
from ansible.module_utils._text import to_text
from ansible.plugins.action import ActionBase

class ActionModule(ActionBase):
	def run(self, tmp=None, task_vars=None):
		if task_vars is None:
			task_vars = dict()
		result = super(ActionModule, self).run(tmp, task_vars)

		state = self._task.args.get('state', None)
		name  = self._task.args.get('name', None)
		domain = self._task.args.get('domain', None)
		ip    = self._task.args.get('ip', None)
		vrack = self._task.args.get('vrack', None)
		boot = self._task.args.get('boot', None)
		force_reboot = self._task.args.get('force_reboot', None)
		template = self._task.args.get('template', None)
		hostname = self._task.args.get('hostname', None)
		service = self._task.args.get('service', None)
		
		result['failed'] = True
		new_src = name
		
		if name is None: 
			result['msg'] = "name is required"
		elif service is None:
			result['msg'] = "service is required"
		else:
			del result['failed']
		if result.get('failed'):
            		return result

		if service == 'template':
			try:
				new_src = self._find_needle('files', name)
            		except AnsibleError as e:
				result['failed'] = True
				result['msg'] = to_text(e)
				return result

		changed = False
		module_return = dict(changed=False)
		module_executed = False

                new_module_args = self._task.args.copy()
                new_module_args.update(
                    dict(
                        name=new_src
                    )
                )
		module_return = self._execute_module(module_name='ovh', module_args=new_module_args, task_vars=task_vars)
		module_executed = True

		if module_return.get('failed'):
			result.update(module_return)
			return result
		if module_return.get('changed'):
			changed = True
		if module_executed:
			result.update(module_return)

		return result
