#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2015 Amir Mofasser <amir.mofasser@gmail.com> (@amimof)

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = """
module: ibmim_installer
version_added: "1.9.4"
short_description: Install/Uninstall IBM Installation Manager
description:
  - Install/Uninstall IBM Installation Manager
options:
  src:
    required: false
    description: Path to installation files for Installation Manager
  dest:
    required: false
    default: "/opt/IBM/InstallationManager"
    description: Path to desired installation directory of Installation Manager
  logdir:
    required: false
    default: "/tmp/"
    description: Path and file name of installation log file
  state:
    required: false
    choices: [ present, absent ]
    default: "present"
    description: Whether Installation Manager should be installed or removed
author: "Amir Mofasser (@amofasser)"
"""

EXAMPLES = """
- name: Install
	ibmim: 
		state: present 
		src: /some/dir/install/
		logdir: /tmp/im_install.log

- name: Uninstall
	ibmim: 
		state: absent
		dest: /opt/IBM/InstallationManager
"""

import os
import subprocess
import platform
import datetime
import socket

class InstallationManagerInstaller():

	module = None
	module_facts = dict(
		im_version = None,
		im_internal_version = None,
		im_arch = None,
		im_header = None
	)

	def __init__(self):
		# Read arguments
	  self.module = AnsibleModule(
	      argument_spec = dict(
	          state   = dict(default='present', choices=['present', 'absent']),
	          src     = dict(required=False),
	          dest    = dict(default="/opt/IBM/InstallationManager/"),
	          logdir  = dict(default="/tmp/")
	      ),
		supports_check_mode=True
	  )


	def getItem(self, str):
		return self.module_facts[str]

	def isProvisioned(self, dest):
		"""
		Checks if Installation Manager is already installed at dest
		:param dest: Installation directory of Installation Manager
		:return: True if already provisioned. False if not provisioned
		"""
		# If destination dir does not exists then its safe to assume that IM is not installed
		if not os.path.exists(dest):
			return False
		else:
			if "installed" in self.getVersion(dest)["im_header"]:
				return True
			return False

	def getVersion(self, dest):
		"""
		Runs imcl with the version parameter and stores the output in a dict
		:param dest: Installation directory of Installation Manager
		:return: dict 
		"""
		child = subprocess.Popen(
			["{0}/eclipse/tools/imcl version".format(dest)],
			shell=True,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE
		)
		stdout_value, stderr_value = child.communicate()

		try:	
			self.module_facts["im_version"] = re.search("Version: ([0-9].*)", stdout_value).group(1)
			self.module_facts["im_internal_version"] = re.search("Internal Version: ([0-9].*)", stdout_value).group(1)
			self.module_facts["im_arch"] = re.search("Architecture: ([0-9].*-bit)", stdout_value).group(1)
			self.module_facts["im_header"] = re.search("Installation Manager.*", stdout_value).group(0)
		except AttributeError:
			pass	

		return self.module_facts

	def main(self):

		state = self.module.params['state']
		src = self.module.params['src']
		dest = self.module.params['dest']
		logdir = self.module.params['logdir']

		if state == 'present':

			if self.module.check_mode:
				self.module.exit_json(changed=False, msg="IBM IM where to be installed at {0}".format(dest))

			# Check if IM is already installed
			if not self.isProvisioned(dest):	

				# Check if paths are valid
				if not os.path.exists(src+"/install"):
					self.module.fail_json(msg=src+"/install not found")

				if not os.path.exists(logdir):
					if not os.listdir(logdir):
						os.makedirs(logdir)

				logfile = "{0}_ibmim_{1}.xml".format(platform.node(), datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
				child = subprocess.Popen(
					["{0}/install "
					 "-acceptLicense "
					 "--launcher.ini {0}/silent-install.ini "
					 "-log {1}/{2} "
					 "-installationDirectory {3}".format(src, logdir, logfile, dest)], 
					shell=True, 
					stdout=subprocess.PIPE, 
					stderr=subprocess.PIPE
				)
				stdout_value, stderr_value = child.communicate()
				if child.returncode != 0:
					self.module.fail_json(
						msg="IBM IM installation failed", 
						stderr=stderr_value, 
						stdout=stdout_value,
						module_facts=self.module_facts
					)

				# Module finished. Get version of IM after installation so that we can print it to the user
				self.getVersion(dest)
				self.module.exit_json(
					msg="IBM IM installed successfully", 
					changed=True, 
					stdout=stdout_value, 
					stderr=stderr_value,
					module_facts=self.module_facts
				)
			else:
				self.module.exit_json(
					changed=False, 
					msg="IBM IM is already installed", 
					module_facts=self.module_facts
				)

		if state == 'absent':

			if self.module.check_mode:
				self.module.exit_json(
					changed=False, 
					msg="IBM IM where to be uninstalled from {0}".format(dest),
					module_facts=self.module_facts
				)
			
			# Check if IM is already installed
			if self.isProvisioned(dest):
				uninstall_dir = "/var/ibm/InstallationManager/uninstall/uninstallc"
				if not os.path.exists("/var/ibm/InstallationManager/uninstall/uninstallc"):
					self.module.fail_json(msg=uninstall_dir + " does not exist")
				child = subprocess.Popen(
					[uninstall_dir],
					shell=True, 
					stdout=subprocess.PIPE,
					stderr=subprocess.PIPE
				)
				stdout_value, stderr_value = child.communicate()
				if child.returncode != 0:
					self.module.fail_json(
						msg="IBM IM uninstall failed", 
						stderr=stderr_value, 
						stdout=stdout_value,
						module_facts=self.module_facts
					)

				# Module finished
				self.module.exit_json(
					changed=True, 
					msg="IBM IM uninstalled successfully", 
					stdout=stdout_value,
					module_facts=self.module_facts
				)
			else:
				self.module.exit_json(
					changed=False, 
					msg="IBM IM is not installed",
					module_facts=self.module_facts
				)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
		imi = InstallationManagerInstaller()
		imi.main()
