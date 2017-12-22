#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2015 Amir Mofasser <amir.mofasser@gmail.com> (@amimof)

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
  wsadmin:
    required: false
    default: True
    description:
      - Use wsadmin to start/stop processes on a node (True) or the native startServer.sh/stopServer.sh on the node machine (False)
author: "Amir Mofasser (@amofasser)"
"""

EXAMPLES = """
# Stop:
- was_server: state=stopped name=AppSrv01 node=devnode wasdir=/usr/local/WebSphere/AppServer/
# Start:
- was_server: state=started name=AppSrv01 node=devnode wasdir=/usr/local/WebSphere/AppServer/
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

def getState(stdout_value, name, wsadmin):
    """
    Does regexp on str to see if wsadmin is returning that the server is running
    :param str: stdout from AdminControl.startServer()
    :param name: name of the application server
    :return: dict
    """

    was_dict["check_stdout"] = stdout_value 
    was_dict["was_name"] = name

    try:
	if wsadmin:
           match = re.search("(Server \"{0}\" is already running)".format(name), stdout_value)
           if match:
               if match.group(0):
                   was_dict["was_state"] = 1
	else:
	   match = re.search("(An instance of the server may already be running: {0})".format(name), stdout_value)
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
            wasdir  = dict(required=True),
	    wsadmin = dict(default=True, type='bool')
        ),
        supports_check_mode = True
    )

    state = module.params['state']
    name = module.params['name']
    node = module.params['node']
    username = module.params['username']
    password = module.params['password']
    wasdir = module.params['wasdir']
    wsadmin = module.params['wsadmin']

    # Check if paths are valid
    if not os.path.exists(wasdir):
        module.fail_json(msg="{0} does not exists".format(wasdir))

    cmd = ""
    credentials = ""
    if username is not None:
	credentials += " {0} -username {1} ".format(credentials, username)
    if password is not None:
  	credentials += " {0} -password {1} ".format(credentials, password)

    # Start server
    if state == 'started':
	if wsadmin: 
	    cmd = "{0}/bin/wsadmin.sh -lang jython {1} -c \"AdminControl.startServer('{2}', '{3}')\"".format(wasdir, credentials, name, node) 
	else:
	    cmd = "{0}/bin/startServer.sh {1} {2}".format(wasdir, name, credentials)
        child = subprocess.Popen(
            [cmd],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE    
        )
        stdout_value, stderr_value = child.communicate()
	if child.returncode != 0:
	    module.fail_json(
		changed=False,
		msg="Failed to start server {0} on node {1}".format(name, node),
		stdout=stdout_value,
		stderr=stderr_value
	    )

        if getState(stdout_value, name, wsadmin)["was_state"] == 1:
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
	if wsadmin:
	   cmd = "{0}/bin/wsadmin.sh -lang jython {1} -c \"AdminControl.stopServer('{2}', '{3}')\"".format(wasdir, credentials, name, node)
	else:
	   cmd = "{0}/bin/stopServer.sh {1} {2}".format(wasdir, name, credentials)
        child = subprocess.Popen(
            [cmd],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE    
        )
        stdout_value, stderr_value = child.communicate()
	if child.returncode != 0:
	    module.fail_json(
		changed=False,
		msg="Failed to stop server {0} on node {1}".format(name, node),
		stdout=stdout_value,
		stderr=stderr_value
	    )
        if getState(stdout_value, name, wsadmin)["was_state"] == 0:
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
