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
    description:
      - Path to installation directory of Installation Manager
  dest:
    required: true
    description:
      - Path to destination installation directory
  im_shared:
    required: true
    description:
      - Path to Installation Manager shared resources folder
  repo:
    required: true
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
- ibmwas: state=present ibmim=/opt/IBM/InstallationManager/ dest=/usr/local/WebSphere/AppServer im_shared=/usr/local/WebSphere/IMShared repo=http://example.com/was-repo/ offering=com.ibm.websphere.ND.v85
# Uninstall:
- ibmwas: state=absent ibmim=/opt/IBM/InstallationManager dest=/usr/local/WebSphere/AppServer/
"""

import os
import subprocess
import platform
import datetime
import shutil

def main():

    # Read arguments
    module = AnsibleModule(
        argument_spec = dict(
            state     = dict(default='present', choices=['present', 'abcent']),
            ibmim     = dict(required=True),
            dest      = dict(required=True),
            im_shared = dict(required=False),
            repo      = dict(required=False),
            offering  = dict(required=True),
            ihs_port  = dict(default=8080),
            logdir    = dict(required=False)
        )
    )

    state = module.params['state']
    ibmim = module.params['ibmim']
    dest = module.params['dest']
    im_shared = module.params['im_shared']
    repo = module.params['repo']
    ihs_port = module.params['ihs_port']
    offering = module.params['offering']
    logdir = module.params['logdir']

    # Check if paths are valid
    if not os.path.exists(ibmim+"/eclipse"):
        module.fail_json(msg=ibmim+"/eclipse not found")

    # Installation
    if state == 'present':
        child = subprocess.Popen([ibmim+"/eclipse/tools/imcl install " + offering + " -repositories " + repo + " -installationDirectory " + dest + " -sharedResourcesDirectory " + im_shared + " -acceptLicense -showProgress -properties user.ihs.httpPort=" + str(ihs_port)], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_value, stderr_value = child.communicate()
        if child.returncode != 0:
            module.fail_json(msg="WAS ND install failed", stdout=stdout_value, stderr=stderr_value)

        module.exit_json(changed=True, msg="WAS ND installed successfully", stdout=stdout_value)

    # Uninstall
    if state == 'abcent':
        if not os.path.exists(logdir):
            if not os.listdir(logdir):
                os.makedirs(logdir)
        logfile = platform.node() + "_wasnd_" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".xml"
        child = subprocess.Popen([ibmim+"/eclipse/IBMIM --launcher.ini " + ibmim + "/eclipse/silent-install.ini -input " + dest + "/uninstall/uninstall.xml -log " + logdir+"/"+logfile], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_value, stderr_value = child.communicate()
        if child.returncode != 0:
            module.fail_json(msg="WAS ND uninstall failed", stdout=stdout_value, stderr=stderr_value)

        # Remove AppServer dir forcefully so that it doesn't prevents us from
        # reinstalling.
        shutil.rmtree(dest, ignore_errors=False, onerror=None)

        module.exit_json(changed=True, msg="WAS ND uninstalled successfully", stdout=stdout_value)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
