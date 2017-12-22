#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2015 Amir Mofasser <amir.mofasser@gmail.com> (@amimof)

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = """
module: profile_dmgr
version_added: "1.9.4"
short_description: Manage a WebSphere Application Server profile
description:
  - Manage a WebSphere Application Server profile
options:
  state:
    required: false
    choices: [ present, absent ]
    default: "present"
    description:
      - The profile should be created or removed
  name:
    required: true
    description:
      - Name of the profile
  wasdir:
    required: true
    description:
      - Path to installation folder of WAS
  cell_name:
    required: false
    description:
      - Cell Name
  host_name:
    required: false
    description:
      - Deployment manager host name
  node_name:
    required: false
    description:
      - Deployment manager node name
  password:
    required: false
    description:
      - Deployment manager password
  username:
    required: false
    description:
      - Deployment manager username
  state:
    required: false
    choices: [ present, absent ]
    default: "present"
    description:
      - The profile should be created or removed
author: "Amir Mofasser (@amofasser)"
"""

EXAMPLES = """
# Install:
profile_dmgr: state=present wasdir=/usr/local/WebSphere name=dmgr cell_name=mycell host_name=dmgr.domain.com node_name=mycell-dmgr username=wasadmin password=waspass
# Uninstall
profile_dmgr: state=absent wasdir=/usr/local/WebSphere name=dmgr
"""

import os
import subprocess
import platform
import datetime
import shutil

def isProvisioned(dest, profileName): 
    """
    Runs manageprofiles.sh -listProfiles command and stores the output in a dict
    :param dest: WAS installation dir
    :param profilesName: Profile Name
    :return: boolean
    """
    if not os.path.exists(dest):
        return False
    else:
        child = subprocess.Popen(
            ["{0}/bin/manageprofiles.sh -listProfiles".format(dest)],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout_value, stderr_value = child.communicate()
        
        if profileName in stdout_value: 
            return True
    return False


def main():

    # Read arguments
    module = AnsibleModule(
        argument_spec = dict(
            state   = dict(default='present', choices=['present', 'absent']),
            wasdir  = dict(required=True),
            name    = dict(required=True),
            cell_name    = dict(required=False),
            host_name = dict(required=False),
            node_name = dict(required=False),
            username = dict(required=False),
            password = dict(required=False)
        )
    )

    state = module.params['state']
    wasdir = module.params['wasdir']
    name = module.params['name']
    cell_name = module.params['cell_name']
    host_name = module.params['host_name']
    node_name = module.params['node_name']
    username = module.params['username']
    password = module.params['password']

    # Check if paths are valid
    if not os.path.exists(wasdir):
        module.fail_json(msg=wasdir+" does not exists")

    # Create a profile
    if state == 'present':
        
        if module.check_mode:
            module.exit_json(
                changed=False, 
                msg="Profile {0} is to be created".format(name)
            )

        if not isProvisioned(wasdir, name):
            child = subprocess.Popen(
                ["{0}/bin/manageprofiles.sh -create "
                "-profileName {1} "
                "-profilePath {0}/profiles/{1} "
                "-templatePath {0}/profileTemplates/management "
                "-cellName {2} "
                "-hostName {3} "
                "-nodeName {4} "
                "-enableAdminSecurity true "
                "-adminUserName {5} "
                "-adminPassword {6} ".format(wasdir, name, cell_name, host_name, node_name, username, password)], 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            stdout_value, stderr_value = child.communicate()
            if child.returncode != 0:
                module.fail_json(
                    msg="Dmgr profile creation failed", 
                    stdout=stdout_value, 
                    stderr=stderr_value
                )

            module.exit_json(
                changed=True, 
                msg="profile {0} created successfully".format(name), 
                stdout=stdout_value,
                stderr=stderr_value
            )
        else:
            module.exit_json(
                changed=False,
                msg="profile {0} already exists".format(name)
            )

    # Remove a profile
    if state == 'absent':
        
        if module.check_mode:
            module.exit_json(
                changed=False, 
                msg="Profile {0} is to be removed".format(name)
        )

        if isProvisioned(wasdir, name):

            child = subprocess.Popen(
                ["{0}/bin/manageprofiles.sh -delete "
                 "-profileName {1}".format(wasdir, name)],
                 shell=True, 
                 stdout=subprocess.PIPE, 
                 stderr=subprocess.PIPE
            )
            stdout_value, stderr_value = child.communicate()
            if child.returncode != 0:
                # manageprofiles.sh -delete will fail if the profile does not exist.
                # But creation of a profile with the same name will also fail if
                # the directory is not empty. So we better remove the dir forcefully.
                if not stdout_value.find("INSTCONFFAILED") < 0:
                    shutil.rmtree("{0}/profiles/{1}".format(wasdir, name), ignore_errors=False, onerror=None)
                else:
                    module.fail_json(
                        msg="Profile {0} removal failed".format(name), 
                        stdout=stdout_value, 
                        stderr=stderr_value
                    )

            module.exit_json(
                changed=True, 
                msg="Profile {0} removed successfully".format(name), 
                stdout=stdout_value, 
                stderr=stderr_value
            )
        else:
            module.exit_json(
                changed=False,
                msg="Profile {0} does not exist".format(name)
            )


# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
