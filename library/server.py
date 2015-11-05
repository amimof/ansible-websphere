#!/usr/bin/python

#
# Author: Amir Mofasser <amir.mofasser@gmail.com>
#
# Stop/Start an Application Server
#
# $IM_INSTALL_DIR/eclipse/tools/imcl install com.ibm.websphere.ND.v85
# -repositories $ND_REPO_DIR
# -installationDirectory $ND_INSTALL_DIR
# -sharedResourcesDirectory $IM_SHARED_INSTALL_DIR
# -acceptLicense -showProgress

import os
import subprocess
import platform
import datetime

def main():

    # Read arguments
    module = AnsibleModule(
        argument_spec = dict(
            state   = dict(default='started', choices=['started', 'stopped']),
            name    = dict(required=True),
            username = dict(required=True),
            password = dict(required=True),
            wasdir  = dict(required=True)
        )
    )

    state = module.params['state']
    name = module.params['name']
    username = module.params['username']
    password = module.params['password']
    wasdir = module.params['wasdir']

    # Check if paths are valid
    if not os.path.exists(wasdir):
        module.fail_json(msg=wasdir+" does not exists")

    # Stop server
    if state == 'stopped':
        child = subprocess.Popen([wasdir+"/bin/stopServer.sh " + name + " -profileName " + name  + " -username " + username + " -password " + password], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_value, stderr_value = child.communicate()
        if child.returncode != 0:
            if not stderr_value.find("appears to be stopped") < 0:
                module.fail_json(msg=name + " stop failed", stdout=stdout_value, stderr=stderr_value)

        module.exit_json(changed=True, msg=name + " stopped successfully", stdout=stdout_value)

    # Start server
    if state == 'started':
        child = subprocess.Popen([wasdir+"/bin/startServer.sh " + name + " -profileName " + name + " -username " + username + " -password " + password], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_value, stderr_value = child.communicate()
        if child.returncode != 0:
            module.fail_json(msg=name + " start failed", stdout=stdout_value, stderr=stderr_value)

        module.exit_json(changed=True, msg=name + " started successfully", stdout=stdout_value)


# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
