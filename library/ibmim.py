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

def main():

    # Read arguments
    module = AnsibleModule(
        argument_spec = dict(
            state   = dict(default='present', choices=['present', 'abcent']),
            src     = dict(required=True),
            dest    = dict(required=False),
            logdir  = dict(required=False)
        )
    )

    state = module.params['state']
    src = module.params['src']
    dest = module.params['dest']
    logdir = module.params['logdir']

    if state == 'present':

        # Check if paths are valid
        if not os.path.exists(src+"/install"):
            module.fail_json(msg=src+"/install not found")
        if not os.path.exists(logdir):
            if not os.listdir(logdir):
                os.makedirs(logdir)

        logfile = platform.node() + "_ibmim_" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".xml"
        child = subprocess.Popen([src+"/install -acceptLicense --launcher.ini "+src+"/silent-install.ini -log " + logdir+"/"+logfile], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_value, stderr_value = child.communicate()
        if child.returncode != 0:
            module.fail_json(msg="IBM IM installation failed", stderr=stderr_value, stdout=stdout_value)

        # Module finished
        module.exit_json(changed=True, msg="IBM IM installed successfully")

    if state == 'abcent':
        uninstall_dir = "/var/ibm/InstallationManager/uninstall/uninstallc"
        if not os.path.exists("/var/ibm/InstallationManager/uninstall/uninstallc"):
            module.fail_json(msg=uninstall_dir + " does not exist")
        child = subprocess.Popen([uninstall_dir], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_value, stderr_value = child.communicate()
        if child.returncode != 0:
            module.fail_json(msg="IBM IM uninstall failed", stderr=stderr_value, stdout=stdout_value)

        # Module finished
        module.exit_json(changed=True, msg="IBM IM uninstalled successfully", stdout=stdout_value)


# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
