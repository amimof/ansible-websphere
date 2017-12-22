#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2015 Amir Mofasser <amir.mofasser@gmail.com> (@amimof)

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
            libertydir  = dict(required=True)
        )
    )

    state = module.params['state']
    name = module.params['name']
    libertydir = module.params['libertydir']

    # Check if paths are valid
    if not os.path.exists(libertydir):
        module.fail_json(msg=libertydir+" does not exists")

    if state == 'stopped':
        child = subprocess.Popen([libertydir+"/bin/server stop " + name], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_value, stderr_value = child.communicate()
        if child.returncode != 0:
            if not stderr_value.find("is not running") < 0:
                module.fail_json(msg=name + " stop failed", stdout=stdout_value, stderr=stderr_value)

        module.exit_json(changed=True, msg=name + " stopped successfully", stdout=stdout_value)

    if state == 'started':
        child = subprocess.Popen([libertydir+"/bin/server start " + name], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_value, stderr_value = child.communicate()
        if child.returncode != 0:
            if not stderr_value.find("is running with process") < 0:
                module.fail_json(msg=name + " start failed", stdout=stdout_value, stderr=stderr_value)

        module.exit_json(changed=True, msg=name + " started successfully", stdout=stdout_value)


# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
