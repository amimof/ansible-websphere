#!/usr/bin/python

#
# Author: Amir Mofasser <amir.mofasser@gmail.com>
#
# This is an Ansible module. Installs/Uninstall IBM Installation Manager
#

DOCUMENTATION = """
module: ibmim
version_added: "1.9.4"
short_description: Install/Uninstall IBM Installation Manager
description:
  - Install/Uninstall IBM Installation Manager
options:
  src:
    required: true
    description:
      - Path to installation files for Installation Manager
  dest:
    required: false
    default: "/opt/IBM/InstallationManager"
    description:
      - Path to desired installation directory of Installation Manager
  logdir:
    required: false
    default: "/tmp/"
    description:
      - Path and file name of installation log file
  state:
    required: false
    choices: [ present, absent ]
    default: "present"
    description:
      - Whether Installation Manager should be installed or removed
author: "Amir Mofasser (@amofasser)"
"""

EXAMPLES = """
# Install:
ibmim: state=present src=/some/dir/install/ logdir=/tmp/im_install.log
# Uninstall
ibmim: state=absent dest=/opt/IBM/InstallationManager
"""

import os
import subprocess
import platform
import datetime
import socket

im_dict = dict(
	im_version = None,
	im_internal_version = None,
	im_arch = None,
	im_header = None
)

def getItem(str):
	return im_dict[str]

def isProvisioned(dest):
	"""
	Checks if Installation Manager is already installed at dest
	:param dest: Installation directory of Installation Manager
	:return: True if already provisioned. False if not provisioned
	"""
	# If destination dir does not exists then its safe to assume that IM is not installed
	if not os.path.exists(dest):
		return False
	else:
		if "installed" in getVersion(dest)["im_header"]:
			return True
		return False

def getVersion(dest):
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
		im_dict["im_version"] = re.search("Version: ([0-9].*)", stdout_value).group(1)
		im_dict["im_internal_version"] = re.search("Internal Version: ([0-9].*)", stdout_value).group(1)
		im_dict["im_arch"] = re.search("Architecture: ([0-9].*-bit)", stdout_value).group(1)
		im_dict["im_header"] = re.search("Installation Manager.*", stdout_value).group(0)
	except AttributeError:
		pass	

	return im_dict

def main():

    # Read arguments
    module = AnsibleModule(
        argument_spec = dict(
            state   = dict(default='present', choices=['present', 'absent']),
            src     = dict(required=True),
            dest    = dict(default="/opt/IBM/InstallationManager/"),
            logdir  = dict(default="/tmp/")
        ),
		supports_check_mode=True
    )

    state = module.params['state']
    src = module.params['src']
    dest = module.params['dest']
    logdir = module.params['logdir']

    if state == 'present':

		if module.check_mode:
			module.exit_json(changed=False, msg="IBM IM where to be installed at {0}".format(dest))

		# Check if IM is already installed
		if not isProvisioned(dest):	

			# Check if paths are valid
			if not os.path.exists(src+"/install"):
				module.fail_json(msg=src+"/install not found")

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
				module.fail_json(msg="IBM IM installation failed", stderr=stderr_value, stdout=stdout_value)

			# Module finished. Get version of IM after installation so that we can print it to the user
			getVersion(dest)
			module.exit_json(changed=True, stdout=stdout_value, stderr=stderr_value,  msg="IBM IM installed successfully", im_version=getItem("im_version"), internal_version=getItem("im_internal_version"), im_arch=getItem("im_arch"), im_header=getItem("im_header"))
		else:
			module.exit_json(changed=False, msg="IBM IM is already installed", im_version=getItem("im_version"), internal_version=getItem("im_internal_version"), im_arch=getItem("im_arch"), im_header=getItem("im_header"))

    if state == 'absent':

		if module.check_mode:
			module.exit_json(changed=False, msg="IBM IM where to be uninstalled from {0}".format(dest))
		
		# Check if IM is already installed
		if isProvisioned(dest):
			uninstall_dir = "/var/ibm/InstallationManager/uninstall/uninstallc"
			if not os.path.exists("/var/ibm/InstallationManager/uninstall/uninstallc"):
				module.fail_json(msg=uninstall_dir + " does not exist")
			child = subprocess.Popen(
				[uninstall_dir],
				shell=True, 
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE
			)
			stdout_value, stderr_value = child.communicate()
			if child.returncode != 0:
				module.fail_json(msg="IBM IM uninstall failed", stderr=stderr_value, stdout=stdout_value)

			# Module finished
			module.exit_json(changed=True, msg="IBM IM uninstalled successfully", stdout=stdout_value)
		else:
			module.exit_json(changed=False, msg="IBM IM is not installed")

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
