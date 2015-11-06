#!/usr/bin/python

#
# Author: Amir Mofasser <amir.mofasser@gmail.com>
#
# This is an Ansible module. Creates a WAS Deployment Manager profile
#
# $WAS_INSTALL_DIR/bin/manageprofiles.sh -create
# -profileName $name
# -profilePath $WAS_INSTALL_DIR/profiles/$name
# -templatePath $WAS_INSTALL_DIR/profileTemplates/management
# -cellName $CELL_NAME
# -hostName $HOST_NAME
# -nodeName $NODE_NAME
# -enableAdminSecurity true
# -adminUserName $ADMIN_USER
# -adminPassword $ADMIN_PASS

import os
import subprocess
import platform
import datetime

def main():

    # Read arguments
    module = AnsibleModule(
        argument_spec = dict(
            state   = dict(default='present', choices=['present', 'abcent']),
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
        child = subprocess.Popen([wasdir+"/bin/manageprofiles.sh -create -profileName " + name + " -profilePath " + wasdir+"/profiles/"+name + " -templatePath " + wasdir+"/profileTemplates/management -cellName " + cell_name + " -hostName " + host_name + " -nodeName " + node_name + " -enableAdminSecurity true -adminUserName " + username + " -adminPassword " + password], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_value, stderr_value = child.communicate()
        if child.returncode != 0:
            module.fail_json(msg="Dmgr profile creation failed", stdout=stdout_value, stderr=stderr_value)

        module.exit_json(changed=True, msg=name + " profile created successfully", stdout=stdout_value)

    # Remove a profile
    if state == 'abcent':
        child = subprocess.Popen([wasdir+"/bin/manageprofiles.sh -delete -profileName " + name], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_value, stderr_value = child.communicate()
        if child.returncode != 0:
            # manageprofiles.sh -delete will fail if the profile does not exist.
            # But creation of a profile with the same name will also fail if
            # the directory is not empty. So we better remove the dir forcefully.
            if not stdout_value.find("INSTCONFFAILED") < 0:
                shutil.rmtree(wasdir+"/profiles/"+name, ignore_errors=False, onerror=None)
            else:
                module.fail_json(msg="Dmgr profile removal failed", stdout=stdout_value, stderr=stderr_value)

        module.exit_json(changed=True, msg=name + " profile removed successfully", stdout=stdout_value, stderr=stderr_value)


# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
