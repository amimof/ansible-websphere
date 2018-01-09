#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2015 Amir Mofasser <amir.mofasser@gmail.com> (@amimof)

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: ibmim
short_description: Manage IBM Installation Manager packages
description: 
	- This module can Install, Uninstall and Update IBM Installation Manager packages on a supported Linux distribution.
	-	This module relies on 'imcl', the binary command line installed by the IM installer. You may use this module to install Installation Manager itself.
version_added: "1.9.4"
author: Amir Mofasser (@github)
requirements:
  - IBM Installation Manager
  - Installation files on remote server or local directory
options:
  id:
		description: The ID of the package which is to be installed
		aliases:
			- name
  ibmim:
		default: /opt/IBM/InstallationManager
		description: Path to installation directory of Installation Manager
  dest:
		description: Path to destination installation directory
  im_shared:
		description: Path to Installation Manager shared resources folder
  repositories:
		description: A list of repositories to use. May be a path, URL or both.
		type: list
		aliases:
			- repos
	preferences:
		type: list
		description: Specify a preference value or a comma-delimited list of preference values to be used
	properties:
		type: list
		description: Specify a preference value or a comma-delimited list of properties values to be used
  state:
		choices: 
			- present
			-	absent
			- latest
		default: present
		description: Install a package with 'present'. Uninstall a package with 'absent'. Update all packages with 'latest'.
	install_fixes:
		choices: 
			- none
			-	recommended
			-	all
		default: none
		description: Install fixes if available in the repositories. 
	connect_passport_advantage:
		default: false
		type: bool
		description: Append the PassportAdvantage repository to the repository list
	log:
		description: Specify a log file that records the result of Installation Manager operations.
'''

EXAMPLES = '''
---
- name: Install WebSphere Application Server Liberty v8.5
  ibmim:
    name: com.ibm.websphere.liberty.v85
    repositories:
			-	http://was-repos/

- name: Uninstall WebSphere Application Server Liberty v8.5
	ibmim:
		name: com.ibm.websphere.liberty.v85
		state: absent

- name: Update all packages
	ibmim:
		state: latest
		repositories:
			- http://was-repos/
'''

import os
import subprocess
import platform
import datetime
import shutil
import re

from ansible.module_utils.basic import AnsibleModule

class InstallationManager():

	module = None
	module_facts = dict(
		installed = False,
		version = None,
		id = None,
		path = None,
		name = None,
		stdout = None,
		stderr = None
	)

	def __init__(self):
		# Read arguments
		self.module = AnsibleModule(
			argument_spec = dict(

				# install/uninstall/updateAll
				state     									= dict(default='present', choices=['present', 'absent', 'latest']),

				# /opt/IBM/InstallationManager
				ibmim     									= dict(default='/opt/IBM/InstallationManager'),

				# Package ID
				id  												= dict(required=False, aliases=['name']),
				
				# -installationDirectory
				dest      									= dict(required=False),

				# -sharedResourcesDirectory
				im_shared 									= dict(required=False),

				# -repositories
				repositories 								= dict(required=False, type='list', aliases=['repos']),

				# -properties
				preferences  								= dict(required=False, type='list'),

				# -properties
				properties  								= dict(required=False, type='list'),
				
				# -connectPassportAdvantage
				connect_passport_advantage 	= dict(default=False, type='bool'),
				
				# -installFixes
				install_fixes 							= dict(default='none', choices=['none', 'recommended', 'all']),

				# -log
				log													= dict(required=False)

			),
			supports_check_mode = True
		)

	def getItem(self, key):
		"""
		Returns an item at key from the global dict module_facts
		"""
		return self.module_facts[key]


	def isProvisioned(self, dest, packageId):
		"""
		Checks if package is already installed at dest
		:param dest: Destination installation directory of the product
		:return: True if already provisioned. False if not provisioned
		"""
		# If destination dir does not exists then its safe to assume that IM is not installed
		if dest:
			if not os.path.exists(dest):
				return False
		return self.getVersion(packageId)["installed"]


	def getVersion(self, packageId):

		child = subprocess.Popen(
			["{0}/eclipse/tools/imcl "
			 " listInstalledPackages "
			 " -long".format(self.module.params['ibmim'])],
			shell=True,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE
		)

		stdout_value, stderr_value = child.communicate()
			
		# Store stdout and stderr
		self.module_facts["stdout"] = stdout_value
		self.module_facts["stderr"] = stderr_value

		if child.returncode != 0:
			self.module.fail_json(
				msg="Error getting installed version of package '{0}'".format(packageId),
				stdout=stdout_value
			)		

		for line in stdout_value.split(os.linesep):
			if packageId in line:
				linesplit = line.split(" : ")
				self.module_facts["installed"] = True
				self.module_facts["path"] = linesplit[0]
				self.module_facts["id"] = linesplit[1]
				self.module_facts["name"] = linesplit[2]
				self.module_facts["version"] = linesplit[3]
				break

		return self.module_facts

	def install(self, module_params):

		# Check mode on
		if self.module.check_mode:
			self.module.exit_json(msg="Package '{0}' is to be installed".format(module_params['id']))

		# Check wether package is already installed
		if self.isProvisioned(module_params['dest'], module_params['id']):
			self.module.exit_json(changed=False, msg="Package '{0}' is already installed".format(module_params['id']), ansible_facts=self.module_facts)

		# Check if one of repositories and connectPassportAdvantage is provided
		if not module_params['repositories'] and not module_params['connect_passport_advantage']:
			self.module.fail_json(msg="One or more repositories are required when installing packages")

		cmd = ("{0}/eclipse/tools/imcl install {1} "
						"-repositories {2} "
						"-acceptLicense "
						"-stopBlockingProcesses ").format(module_params['ibmim'], module_params['id'], ",".join(module_params['repositories']))

		if module_params['dest']:
			cmd = "{0} -installationDirectory {1} ".format(cmd, module_params['dest'])
		if module_params['im_shared']:
			cmd = "{0} -sharedResourcesDirectory {1} ".format(cmd, module_params['im_shared'])
		if module_params['properties']: 
			cmd = "{0} -properties {1} ".format(cmd, ",".join(module_params['properties']))
		if module_params['preferences']: 
			cmd = "{0} -preferences {1} ".format(cmd, ",".join(module_params['preferences']))
		if module_params['install_fixes']:
			cmd = "{0} -installFixes {1} ".format(cmd, module_params['install_fixes'])
		if module_params['connect_passport_advantage']:
			cmd = "{0} -connectPassportAdvantage ".format(cmd)
		if module_params['log']:
			cmd = "{0} -log {1} ".format(cmd, module_params['log'])

		child = subprocess.Popen(
			[cmd], 
			shell=True, 
			stdout=subprocess.PIPE, 
			stderr=subprocess.PIPE
		)

		stdout_value, stderr_value = child.communicate()
		if child.returncode != 0:
			self.module.fail_json(
				msg="Failed installing package '{0}'".format(module_params['id']),
				stdout=stdout_value,
				stderr=stderr_value
		)

		# After install, get versionInfo so that we can show it to the user
		self.getVersion(module_params['id'])
		self.module.exit_json(changed=True, msg="Package '{0}' installed".format(module_params['id']), ansible_facts=self.module_facts)

	def uninstall(self, module_params):

		# CHeck mode on
		if self.module.check_mode:
			self.module.exit_json(changed=False, msg="Package '{0}' is to be uninstalled".format(module_params['id']), ansible_facts=self.module_facts)

		# Check wether package is installed
		if not self.isProvisioned(module_params['dest'], module_params['id']):
			self.module.exit_json(changed=False, msg="Package '{0}' is not installed".format(module_params['id']), ansible_facts=self.module_facts)

		cmd = "{0}/eclipse/tools/imcl uninstall {1} ".format(module_params['ibmim'], module_params['id'])

		if module_params['dest']:
			cmd = "{0} -installationDirectory {1} ".format(cmd, module_params['dest'])
		if module_params['preferences']:
			cmd = "{0} -preferences {1} ".format(cmd, ",".join(module_params['preferences']))
		if module_params['properties']:
			cmd = "{0} -properties {1} ".format(cmd, ",".join(module_params['properties']))
		if module_params['log']:
			cmd = "{0} -log {1} ".format(cmd, module_params['log'])

		child = subprocess.Popen(
			[cmd], 
			shell=True, 
			stdout=subprocess.PIPE, 
			stderr=subprocess.PIPE
		)
		stdout_value, stderr_value = child.communicate()
		if child.returncode != 0:
			self.module.fail_json(msg="Failed uninstalling package '{0}'".format(module_params['id']))

		# Remove AppServer dir forcefully so that it doesn't prevents us from reinstalling.
		shutil.rmtree(module_params['dest'], ignore_errors=False, onerror=None)
		self.module.exit_json(changed=True, msg="Package '{0}' uninstalled".format(module_params['id']), ansible_facts=self.module_facts)

	def updateAll(self, module_params):

		# Check mode on
		if self.module.check_mode:
			self.module.exit_json(changed=False, msg="All installed packages are to be updated".format(module_params['id']), ansible_facts=self.module_facts)

		# Check if one of repositories and connectPassportAdvantage is provided
		if not module_params['repositories'] and not module_params['connect_passport_advantage']:
			self.module.fail_json(msg="One or more repositories are required when installing packages")

		cmd = ("{0}/eclipse/tools/imcl updateAll "
						"-acceptLicense -repositories {1}").format(module_params['ibmim'], ",".join(module_params['repositories']))

		if module_params['preferences']:
			cmd = "{0} -preferences {1} ".format(cmd, ",".join(module_params['preferences']))
		if module_params['properties']:
			cmd = "{0} -properties {1} ".format(cmd, ",".join(module_params['properties']))
		if module_params['connect_passport_advantage']:
			cmd = "{0} -connectPassportAdvantage ".format(cmd)
		if module_params['install_fixes']:
			cmd = "{0} -installFixes {1} ".format(cmd, module_params['install_fixes'])
		if module_params['log']:
			cmd = "{0} -log {1} ".format(cmd, module_params['log'])

		child = subprocess.Popen(
			[cmd], 
			shell=True, 
			stdout=subprocess.PIPE, 
			stderr=subprocess.PIPE
		)
		stdout_value, stderr_value = child.communicate()
		
		if child.returncode != 0:
			self.module.fail_json(msg="Failed updating packages", stdout=stdout_value, stderr=stderr_value)		

		self.module.exit_json(changed=True, msg="All packages updated", ansible_facts=self.module_facts)

	def main(self):

		# Check if paths are valid
		if not os.path.exists("{0}/eclipse".format(self.module.params['ibmim'])):
			self.module.fail_json(
				msg="IBM Installation Manager is not installed. Install it and try again.")
		
		# Install
		if self.module.params['state'] == 'present':
				self.install(self.module.params)
				
		# Uninstall
		if self.module.params['state'] == 'absent':
				self.uninstall(self.module.params)

		# Update everything
		if self.module.params['state'] == 'latest':
				self.updateAll(self.module_params)

# import module snippets
if __name__ == '__main__':
	im = InstallationManager()
	im.main()