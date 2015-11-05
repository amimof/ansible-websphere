#!/usr/bin/python

#
# Author: Amir Mofasser <amir.mofasser@gmail.com>
#
# This is an Ansible module. Creates a Liberty server
#
# server create server_name
#

import os
import subprocess

def main():

    # Read arguments
    module = AnsibleModule(
        argument_spec = dict(
            state   = dict(default='present', choices=['present', 'abcent']),
            libertydir  = dict(required=True),
            name    = dict(required=True),
        )
    )

    state = module.params['state']
    libertydir = module.params['libertydir']
    name = module.params['name']

    # Check if paths are valid
    if not os.path.exists(libertydir):
        module.fail_json(msg=libertydir+" does not exists")

    # Create a profile
    if state == 'present':
        child = subprocess.Popen([libertydir+"/bin/server create " + name], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_value, stderr_value = child.communicate()
        if child.returncode != 0:
            module.fail_json(msg="Failed to create liberty server " + name, stdout=stdout_value, stderr=stderr_value)

        module.exit_json(changed=True, msg=name + " server created successfully", stdout=stdout_value)

    # Remove a profile
    if state == 'abcent':
        child = subprocess.Popen(["rm -rf " + libertydir+"/usr/servers/" + name], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_value, stderr_value = child.communicate()
        if child.returncode != 0:
                module.fail_json(msg="Dmgr profile removal failed", stdout=stdout_value, stderr=stderr_value)

        module.exit_json(changed=True, msg=name + " server removed successfully", stdout=stdout_value, stderr=stderr_value)


# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
