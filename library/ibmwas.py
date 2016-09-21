#!/usr/bin/python

#
# Author: Amir Mofasser <amir.mofasser@gmail.com>
#
# This is an Ansible module. Installs/Uninstall IBM WebSphere Application Server Binaries
#
# $IM_INSTALL_DIR/eclipse/tools/imcl install com.ibm.websphere.ND.v85
# -repositories $ND_REPO_DIR
# -installationDirectory $ND_INSTALL_DIR
# -sharedResourcesDirectory $IM_SHARED_INSTALL_DIR
# -acceptLicense -showProgress

DOCUMENTATION = """
module: ibmwas
version_added: "1.9.4"
short_description: Install/Uninstall WebSphere Application Server
description:
  - Install/Uninstall WebSphere Application Server using Installation Manager
options:
  ibmim:
	required: true
	default: '/opt/IBM/InstallationManager'
	description:
	  - Path to installation directory of Installation Manager
  dest:
	required: true
	description:
	  - Path to destination installation directory
  im_shared:
	required: false
	description:
	  - Path to Installation Manager shared resources folder
  ihs_port:
	required: false
	default: 8080
	description:
	  - IHS default listening port. Only applicable when installing IBM HTTP Server
  repo:
	required: false
	description:
	  - URL or path to the installation repository used by Installation Manager to install WebSphere products
  offering:
	required: true
	description:
	  - Name of the offering which you want to install
  state:
	required: false
	choices: [ present, absent ]
	default: "present"
	description:
	  - Whether WAS should be installed or removed
notes:
  - IBM Installation Manager is required to install WebSphere products using this module
  - Assumes access to installation files on remote server or local directory
author: "Amir Mofasser (@amofasser)"
"""

EXAMPLES = """
# Install:
- ibmwas: state=present ibmim=/opt/IBM/InstallationManager/ dest=/usr/local/WebSphere/AppServer repo=http://example.com/was-repo/ offering=com.ibm.websphere.ND.v85
# Uninstall:
- ibmwas: state=absent ibmim=/opt/IBM/InstallationManager dest=/usr/local/WebSphere/AppServer/
"""

import os
import subprocess
import platform
import datetime
import shutil
import re

was_dict = dict(
	was_name = None,
	was_version = None,
	was_id = None,
	was_arch = None,
	was_installed = False,
	check_stdout = None,
	check_stderr = None
)

def getItem(str):
	return was_dict[str]

def isProvisioned(dest, offering):
	"""
	Checks if WebSphere Application Server is already installed at dest
	:param dest: Installation directory of WAS
	:return: True if already provisioned. False if not provisioned
	"""
	# If destination dir does not exists then its safe to assume that IM is not installed
	if not os.path.exists(dest):
		return False
	return getVersion(dest, offering)["was_installed"]

def getVersion(dest, offering):
	"""
	Runs versionInfo.sh and stores the output in a dict
	:param dest: Installation directory of WAS
	:return: dict
	"""
	versioncmd = None
	wasversion = None
	versionpwd = None
	installed = False



	# Build the command to execute in order to get version information
	# Start by checking for specific product offering since some IBM products differ in 
	# how to get version information.
	if "com.ibm.websphere.liberty".lower() in offering.lower():
		# Liberty uses productInfo to return version number of the product
		if os.path.isfile("{0}/bin/productInfo".format(dest)):
			versioncmd = "productInfo version"
			wasversion = "liberty"
			versionpwd = "{0}/bin/".format(dest)
			installed = True
	elif "com.ibm.websphere.IBMJAVA".lower() in offering.lower():
		# Java is version is retrieved the by simple java -version
		for d in os.listdir("{0}/".format(dest)):
			match = re.search("(java_.*)", d)
			if match:
				if match.group(0) in d:
					if os.path.isfile("{0}/{1}/bin/java".format(dest, d)):
						versioncmd = "java -version"
						wasversion = "java"	
						versionpwd = "{0}/{1}/bin/".format(dest, d)
						installed = True
	else:
		# If none above is true then lets assume that the desired product is a WAS specific product
		if os.path.isfile("{0}/bin/versionInfo.sh".format(dest)):
			versioncmd = "versionInfo.sh"
			wasversion = "was"
			versionpwd = "{0}/bin/".format(dest)
			installed = True

	child = subprocess.Popen(
		["{0}/{1}".format(versionpwd, versioncmd)],
		shell=True,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE
	)

	stdout_value, stderr_value = child.communicate()
		
	was_dict["check_stdout"] = stdout_value
	was_dict["check_stderr"] = stderr_value

	try:
		if wasversion == "was":
			was_dict["was_name"] = re.search("(Name\s*)(.*[a-z]|[A-Z].*)", stdout_value).group(2)
			was_dict["was_version"] = re.search("(Version\s*)(.*[0-9].[0-9].[0-9].[0-9].*)", stdout_value).group(2)
			was_dict["was_id"] = re.search("(ID\s*)(.*[a-z]|[A-Z].*)", stdout_value).group(2)
			was_dict["was_arch"] = re.search("(Architecture\s*)(.*)", stdout_value).group(2)
			was_dict["was_installed"] = installed
		if wasversion == "liberty":
			was_dict["was_name"] = re.search("(Product name:.)(.*[a-z]|[A-Z]*)", stdout_value).group(2)
			was_dict["was_version"] = re.search("(Product version:.*)(.*[0-9].[0-9].[0-9].[0-9].*)", stdout_value).group(2)
			was_dict["was_id"] = re.search("(Product edition:.)(.*[a-z]|[A-Z]*)", stdout_value).group(2)
			was_dict["was_installed"] = installed
		if wasversion == "java":
			was_dict["was_name"] = "Java SE Runtime Environment"
			was_dict["was_version"] = stdout_value
			was_dict["was_installed"] = installed
	except AttributeError:
		raise

	return was_dict


def main():

	# Read arguments
	module = AnsibleModule(
		argument_spec = dict(
			state     = dict(default='present', choices=['present', 'absent']),
			ibmim     = dict(default='/opt/IBM/InstallationManager'),
			dest      = dict(required=True),
			im_shared = dict(required=False),
			repo      = dict(required=False),
			offering  = dict(required=True),
			ihs_port  = dict(default=8080)
		),
		supports_check_mode = True
	)

	state = module.params['state']
	ibmim = module.params['ibmim']
	dest = module.params['dest']
	im_shared = module.params['im_shared']
	repo = module.params['repo']
	ihs_port = module.params['ihs_port']
	offering = module.params['offering']

	# Check if paths are valid
	if not os.path.exists("{0}/eclipse".format(ibmim)):
		module.fail_json(msg="{0}/eclipse not found. Make sure IBM Installation Manager is installed and that ibmim is pointing to correct directory.".format(ibmim))
	
	# Install
	if state == 'present':
		
		if module.check_mode:
			module.exit_json(changed=False, msg="WebSphere Application Server is to be installed at {0}".format(dest))

		# Check wether was is already installed
		if not isProvisioned(dest, offering):

			child = subprocess.Popen(
				["{0}/eclipse/tools/imcl install {1} "
				 "-repositories {2} "
				 "-installationDirectory {3} " 
				 "-sharedResourcesDirectory {4} "
				 "-properties user.ihs.httpPort={5} "
				 "-showProgress "
				 "-acceptLicense "
				 "-stopBlockingProcesses".format(ibmim, offering, repo, dest, im_shared, str(ihs_port))], 
				shell=True, 
				stdout=subprocess.PIPE, 
				stderr=subprocess.PIPE
			)
			stdout_value, stderr_value = child.communicate()
			if child.returncode != 0:
				module.fail_json(
					changed=False, 
					msg="WebSphere Application Server installation failed", 
					stdout=stdout_value, 
					stderr=stderr_value
				)

			# After install, get versionInfo so that we can show it to the user
			getVersion(dest, offering)
			module.exit_json(
				changed=True, 
				msg="WAS ND installed successfully", 
				stdout=stdout_value, 
				stderr=stderr_value,
				was_name=getItem("was_name"), 
				was_version=getItem("was_version"), 
				was_id=getItem("was_id"), 
				was_arch=getItem("was_arch"), 
				was_installed=getItem("was_installed")
			)
		else:
			module.exit_json(
				changed=False, 
				msg="WebSphere Application Server is already installed", 
				stdout=getItem("check_stdout"),
				stderr=getItem("check_stderr"),
				was_name=getItem("was_name"), 
				was_version=getItem("was_version"), 
				was_id=getItem("was_id"), 
				was_arch=getItem("was_arch"), 
				was_installed=getItem("was_installed")
			)

	# Uninstall
	if state == 'absent':

		if module.check_mode:
			module.exit_json(changed=False, msg="WebSphere Application Server is to be uninstalled from {0}".format(dest))

		# Check wether was is installed
		if isProvisioned(dest, offering):
			
			child = subprocess.Popen(
				["{0}/eclipse/tools/imcl uninstall {1} "
				 "-installationDirectory {2}".format(ibmim, offering, dest)], 
				shell=True, 
				stdout=subprocess.PIPE, 
				stderr=subprocess.PIPE
			)
			stdout_value, stderr_value = child.communicate()
			if child.returncode != 0:
				module.fail_json(msg="WebSphere Application Server uninstall failed", stdout=stdout_value, stderr=stderr_value)

			# Remove AppServer dir forcefully so that it doesn't prevents us from reinstalling.
			shutil.rmtree(dest, ignore_errors=False, onerror=None)
			module.exit_json(changed=True, msg="WebSphere Application Server uninstalled successfully", stdout=stdout_value, stderr=stderr_value)

		else:
			module.exit_json(changed=False, msg="WebSPhere Application Server is not installed")

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
	main()
