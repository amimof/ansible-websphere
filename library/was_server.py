#!/usr/bin/python

#
# Author: Amir Mofasser <amir.mofasser@gmail.com>
#
# Stop/Start a WebSphere Application Server
#

DOCUMENTATION = """
module: was_server
version_added: "1.9.4"
short_description: Stop/Start a WebSphere Application Server on a node
description:
  - Stop/Start a WebSphere Application Server on a node
options:
  state:
    required: false
    default: started
    description:
      - Whether WAS should be stopped or started
  name:
    required: true
    description:
      - Name of the application server
  node:
    required: true
    description:
      - Name of the node on which the application server is running on
  username:
    required: false
    description:
      - Administrative user username 
  password:
    required: false
    description:
      - Administrative user password
  wasdir:
    required: true
    description:
      - Path to root of WAS installation directory 
author: "Amir Mofasser (@amofasser)"
"""

EXAMPLES = """
# Stop:
- was_server: state=stopped wasdir=/usr/local/WebSphere/AppServer 
# Start:
- was_server: state=started wasdir=/usr/local/WebSphere/AppServer/
"""

import os
import subprocess
import platform
import datetime

was_dict = dict(
    was_name = None,
    was_state = 0,
    check_stdout = None
)

def getItem(str):
    return was_dict[str]

def getState(stdout_value, name):
    """
    Does regexp on str to see if wsadmin is returning that the server is running
    :param str: stdout from AdminControl.startServer()
    :param name: name of the application server
    :return: dict
    """

    was_dict["check_stdout"] = stdout_value 
    was_dict["was_name"] = name

    try:
        match = re.search("(Server \"{0}\" is already running)".format(name), stdout_value)
        if match:
            if match.group(0):
                was_dict["was_state"] = 1

    except AttributeError:
        raise

    return was_dict


def main():

    # Read arguments
    module = AnsibleModule(
        argument_spec = dict(
            state   = dict(default='started', choices=['started', 'stopped']),
            name    = dict(required=True),
            node = dict(required=True),
            username = dict(required=False),
            password = dict(required=False),
            wasdir  = dict(required=True)
        ),
        supports_check_mode = True
    )

    state = module.params['state']
    name = module.params['name']
    node = module.params['node']
    username = module.params['username']
    password = module.params['password']
    wasdir = module.params['wasdir']

    # Check if paths are valid
    if not os.path.exists(wasdir):
        module.fail_json(msg="{0} does not exists".format(wasdir))

    # Start server
    if state == 'started'
        child = subprocess.Popen(
            ["{0}/bin/wsadmin.sh -lang jython "
             "-username '{1}' "
             "-password '{2}' "
             "-c AdminControl.startServer('{3}', '{4}')".format(wasdir, username, password, name, node)],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE    
        )
        stdout_value, stderr_value = child.communicate()
        if getState(stdout_value, name)[was_state] == 1:
            module.exit_json(
                changed=False,
                msg="Server {0} is already started".format(name),
                stdout=stdout_value,
                stderr=stderr_value,
                was_name=getItem("was_name"),
                was_state=getItem("was_state"),
                check_stdout=getItem("check_stdout")
            )
        else: 
            module.exit_json(
                changed=False,
                msg="Server {0} successfully started".format(name),
                stdout=stdout_value,
                stderr=stderr_value,
                was_name=getItem("was_name"),
                was_state=getItem("was_state"),
                check_stdout=getItem("check_stdout")
            )

    # Stop server
    if state == 'stopped':
        child = subprocess.Popen(
            ["{0}/bin/wsadmin.sh -lang jython "
             "-username '{1}' "
             "-password '{2}' "
             "-c AdminControl.stopServer('{3}', '{4}')".format(wasdir, username, password, name, node)],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE    
        )
        stdout_value, stderr_value = child.communicate()
        if getState(stdout_value, name)[was_state] == 0:
            module.exit_json(
                changed=False,
                msg="Server {0} is already stopped".format(name),
                stdout=stdout_value,
                stderr=stderr_value,
                was_name=getItem("was_name"),
                was_state=getItem("was_state"),
                check_stdout=getItem("check_stdout")
            )
        else:
            module.exit_json(
                changed=False,
                msg="Server {0} successfully stopped".format(name),
                stdout=stdout_value,
                stderr=stderr_value,
                was_name=getItem("was_name"),
                was_state=getItem("was_state"),
                check_stdout=getItem("check_stdout")
            )

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
