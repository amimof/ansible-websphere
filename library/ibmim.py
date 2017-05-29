#!/usr/bin/python

# Author: Amir Mofasser <amir.mofasser@gmail.com>
#
# This is an Ansible module. Installs/Uninstall IBM WebSphere Application Server Binaries
#
# $IM_INSTALL_DIR/eclipse/tools/imcl install com.ibm.websphere.ND.v85
# -repositories $ND_REPO_DIR
# -installationDirectory $ND_INSTALL_DIR
# -sharedResourcesDirectory $IM_SHARED_INSTALL_DIR
# -acceptLicense -showProgress

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: ibmim
version_added: "1.9.4"
short_description: Manage IBM Installation Manager packages
description: Install, Update and Uninstall Installation Manager packages using remote or local repositories
options:
  id:
		required: true
		description: Name of the package which is to be installed
  ibmim:
		required: false
		default: '/opt/IBM/InstallationManager'
		description: Path to installation directory of Installation Manager
  dest:
		required: false
		description: Path to destination installation directory
  im_shared:
		required: false
		description: Path to Installation Manager shared resources folder
  repositories:
		required: false
		description: Comma separated list of repositories to use. May be a path, URL or both
  state:
		required: false
		choices: [ present, absent, update ]
		default: present
		description: Install a package with 'present'. Uninstall a package with 'absent'. Update all packages with 'update'.
	install_fixes:
		required: false
		choices: [ none, recommended, all ]
		default: none
		description: Install fixes if available in the repositories. 
	connect_passport_advantage
		required: false
		default: false
		description: Append the PassportAdvantage repository to the repository list
requirements:
  - IBM Installation Manager
  - Installation files on remote server or local directory
author: "Amir Mofasser (@amofasser)"
"""

EXAMPLES = """
- name: Install WebSphere Application Server Liberty v8.5
  ibmim:
    id: com.ibm.websphere.liberty.BASE.v85
    repositories: /var/data/was

- name: Uninstall WebSphere Application Server Liberty v8.5
	ibmim:
		id: com.ibm.websphere.liberty.BASE.v85
		state: absent

- name: Update all packages
	ibmim:
		id: null
		state: update
		repositories: /var/data/was
"""

import os
import subprocess
import platform
import datetime
import shutil
import re

class InstallationManager():

	module = None
	module_facts = dict(
		installed = False,
		version = None,
		id = None,
		path = None,
		name = None,
		check_stdout = None,
		check_stderr = None
	)

	def __init__(self):
		# Read arguments
		self.module = AnsibleModule(
			argument_spec = dict(

				# install/uninstall/updateAll
				state     									= dict(default='present', choices=['present', 'absent', 'update']),

				# /opt/IBM/InstallationManager
				ibmim     									= dict(default='/opt/IBM/InstallationManager'),

				# Package ID
				id  												= dict(required=True),
				
				# -installationDirectory
				dest      									= dict(required=False),

				# -sharedResourcesDirectory
				im_shared 									= dict(required=False),

				# -repositories
				repositories 								= dict(required=False),

				# -properties
				properties  								= dict(required=False),
				
				# -connectPassportAdvantage
				connect_passport_advantage 	= dict(default=False, type='bool'),
				
				# -installFixes
				install_fixes 							= dict(default='none', choices=['none', 'recommended', 'all'])

			),
			supports_check_mode = True
		)

	def getItem(self, key):
		"""
		Returns an item at key from the global dict module_facts
		"""
		return self.module_facts[key]


	def isProvisioned(self, dest, pacakgeId):
		"""
		Checks if package is already installed at dest
		:param dest: Destination installation directory of the product
		:return: True if already provisioned. False if not provisioned
		"""
		# If destination dir does not exists then its safe to assume that IM is not installed
		if dest:
			if not os.path.exists(dest):
				return False
		return self.getVersion(pacakgeId)["installed"]


	def getVersion(self, pacakgeId):

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
		self.module_facts["check_stdout"] = stdout_value
		self.module_facts["check_stderr"] = stderr_value

		if child.returncode != 0:
			self.module.fail_json(
				msg="Error getting installed version of package '{0}'".format(pacakgeId),
				stdout=stdout_value,
				stderr=stderr_value,

			)		

		for line in stdout_value.split(os.linesep):
			if pacakgeId in line:
				linesplit = line.split(" : ")
				self.module_facts["installed"] = True
				self.module_facts["path"] = linesplit[0]
				self.module_facts["id"] = linesplit[1]
				self.module_facts["name"] = linesplit[2]
				self.module_facts["version"] = linesplit[3]
				break

		return self.module_facts


	def main(self):

		state = self.module.params['state']
		ibmim = self.module.params['ibmim']
		dest = self.module.params['dest']
		im_shared = self.module.params['im_shared']
		repositories = self.module.params['repositories']
		pacakgeId = self.module.params['id']
		properties = self.module.params['properties']
		installFixes = self.module.params['install_fixes']
		connectPassportAdvantage = self.module.params['connect_passport_advantage']

		# Check if paths are valid
		if not os.path.exists("{0}/eclipse".format(ibmim)):
			self.module.fail_json(
				msg="{0}/eclipse not found. Make sure IBM Installation Manager is installed and that ibmim is pointing to correct directory.".format(ibmim),
				module_facts=self.module_facts
			)
		
		# Install
		if state == 'present':
			
			if self.module.check_mode:
				self.module.exit_json(
					changed=False, 
					msg="Package '{0}' is to be installed".format(pacakgeId),
					module_facts=self.module_facts
				)

			# Check wether pacakge is already installed
			if not self.isProvisioned(dest, pacakgeId):

				if not repositories:
					self.module.fail_json(
						changed=False,
						msg="Param repositories is required when installing packages",
						module_facts=self.module_facts
					)

				cmd = ("{0}/eclipse/tools/imcl install {1} "
							 "-repositories {2} "
							 "-acceptLicense "
							 "-stopBlockingProcesses ").format(ibmim, pacakgeId, repositories)

				if dest:
					cmd = "{0} -installationDirectory {1} ".format(cmd, dest)
				if im_shared:
					cmd = "{0} -sharedResourcesDirectory {1} ".format(cmd, im_shared)
				if properties: 
					cmd = "{0} -properties {1} ".format(cmd, properties)
				if installFixes:
					cmd = "{0} -installFixes {1} ".format(cmd, installFixes)
				if connectPassportAdvantage:
					cmd = "{0} -connectPassportAdvantage ".format(cmd)

				child = subprocess.Popen(
					[cmd], 
					shell=True, 
					stdout=subprocess.PIPE, 
					stderr=subprocess.PIPE
				)
				stdout_value, stderr_value = child.communicate()
				if child.returncode != 0:
					self.module.fail_json(
						changed=False, 
						msg="Failed installing package '{0}'".format(pacakgeId), 
						stdout=stdout_value, 
						stderr=stderr_value,
						module_facts=self.module_facts
					)

				# After install, get versionInfo so that we can show it to the user
				self.getVersion(pacakgeId)
				self.module.exit_json(
					changed=True, 
					msg="Package '{0}' installed successfully".format(pacakgeId), 
					stdout=stdout_value, 
					stderr=stderr_value,
					module_facts=self.module_facts
				)
			
			else:

				self.module.exit_json(
					changed=False, 
					msg="Package '{0}' is already installed".format(pacakgeId), 
					stdout=self.getItem("check_stdout"),
					stderr=self.getItem("check_stderr"),
					module_facts=self.module_facts
				)
				


		# Uninstall
		if state == 'absent':

			if self.module.check_mode:
				self.module.exit_json(
					changed=False,
					msg="Package '{0}' is to be uninstalled".format(pacakgeId),
					module_facts=self.module_facts
				)

			# Check wether was is installed
			if self.isProvisioned(dest, pacakgeId):

				cmd = "{0}/eclipse/tools/imcl uninstall {1} ".format(ibmim, pacakgeId)

				if dest:
					cmd = "{0} -installationDirectory {1} ".format(cmd, dest)
				if properties:
					cmd = "{0} -properties {1} ".format(cmd, properties)
				if preferences:
					cmd = "{0} -preferences {1} ".format(cmd, preferences)

				child = subprocess.Popen(
					[cmd], 
					shell=True, 
					stdout=subprocess.PIPE, 
					stderr=subprocess.PIPE
				)
				stdout_value, stderr_value = child.communicate()
				if child.returncode != 0:
					self.module.fail_json(
						msg="Failed uninstalling package '{0}'".format(pacakgeId), 
						stdout=stdout_value, 
						stderr=stderr_value,
						module_facts=self.module_facts
					)

				# Remove AppServer dir forcefully so that it doesn't prevents us from reinstalling.
				shutil.rmtree(dest, ignore_errors=False, onerror=None)
				self.module.exit_json(
					changed=True,
					msg="Package '{0}' uninstalled successfully".format(pacakgeId), 
					stdout=stdout_value, 
					stderr=stderr_value,
					module_facts=self.module_facts
				)

			else:
				self.module.exit_json(
					changed=False, 
					msg="Package '{0}' is not installed".format(pacakgeId),
					module_facts=self.module_facts
				)
		if state == 'update':

			if self.module.check_mode:
				self.module.exit_json(
					changed=False, 
					msg="All installed packages are to be updated".format(pacakgeId),
					module_facts=self.module_facts
				)

			if not repositories:
				self.module.fail_json(
					changed=False,
					msg="Param repositories is required when updating packages",
					module_facts=self.module_facts
				)

			cmd = ("{0}/eclipse/tools/imcl updateAll "
						 "-repositories {1}").format(ibmim, repositories)

			if properties:
				cmd = "{0} -properties {1} ".format(cmd, properties)
			if connectPassportAdvantage:
				cmd = "{0} -connectPassportAdvantage ".format(cmd)
			if installFixes:
				cmd = "{0} -installFixes {1} ".format(cmd, installFixes)


			child = subprocess.Popen(
				[cmd], 
				shell=True, 
				stdout=subprocess.PIPE, 
				stderr=subprocess.PIPE
			)
			stdout_value, stderr_value = child.communicate()
			if child.returncode != 0:
				self.module.fail_json(
					msg="Failed updating packages", 
					stdout=stdout_value, 
					stderr=stderr_value,
					module_facts=self.module_facts
				)		

			self.module.exit_json(
				changed=True,
				msg="All packages updated",
				stdout=stdout_value,
				stderr=stderr_value,
				module_facts=self.module_facts
			)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
	im = InstallationManager()
	im.main()
