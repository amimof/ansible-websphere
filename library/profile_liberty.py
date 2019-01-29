#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2015 Amir Mofasser <amir.mofasser@gmail.com> (@amimof)

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import subprocess

def main():

    # Read arguments
    module = AnsibleModule(
        argument_spec = dict(
            state   = dict(default='present', choices=['present', 'absent']),
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
    if state == 'absent':
        child = subprocess.Popen(["rm -rf " + libertydir+"/usr/servers/" + name], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_value, stderr_value = child.communicate()
        if child.returncode != 0:
                module.fail_json(msg="Dmgr profile removal failed", stdout=stdout_value, stderr=stderr_value)

        module.exit_json(changed=True, msg=name + " server removed successfully", stdout=stdout_value, stderr=stderr_value)


# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
