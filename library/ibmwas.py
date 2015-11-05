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

import os
import subprocess
import platform
import datetime
import shutil

def main():

    # WAS offerings
    offerings = [
        'com.ibm.websphere.ND.v85',
        'com.ibm.websphere.IHS.v85',
        'com.ibm.websphere.PLG.v85',
        'com.ibm.websphere.WCT.v85',
        'com.ibm.websphere.liberty.IBMJAVA.v70',
        'com.ibm.websphere.liberty.v85'
    ]

    # Read arguments
    module = AnsibleModule(
        argument_spec = dict(
            state     = dict(default='present', choices=['present', 'abcent']),
            ibmim     = dict(required=True),
            dest      = dict(required=True),
            im_shared = dict(required=False),
            repo      = dict(required=False),
            offering  = dict(default='com.ibm.websphere.ND.v85', choices=offerings),
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
