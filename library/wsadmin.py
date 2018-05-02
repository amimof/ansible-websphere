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
            params = dict(required=True),
            host = dict(default='localhost', required=False),
            port = dict(default='8879', required=False),
            username = dict(required=False),
            password = dict(required=False),
            script = dict(required=True)
        )
    )

    params = module.params['params']
    host = module.params['host']
    port = module.params['port']
    username = module.params['username']
    password = module.params['password']
    script = module.params['script']

    # Run wsadmin command server
    if state == 'stopped':
        child = subprocess.Popen([wasdir+"/bin/wsadmin.sh -lang jython -conntype SOAP -host "+host+" -port "+port+" -username " + username + " -password " + password " -f "+script+" "+params], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_value, stderr_value = child.communicate()
        if child.returncode != 0:
            module.fail_json(msg="Failed executing wsadmin script: " + ¨script, stdout=stdout_value, stderr=stderr_value)

        module.exit_json(changed=True, msg="Script executed successfully: " + script, stdout=stdout_value)


# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
