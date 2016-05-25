# README
This library of Ansible modules lets you provision and configure WebSphere Application Server including WebSphere Liberty Profile. All products are installed using IBM Installation Manager which is installed with the module, `ibmim.py`. The products are then installed using Installation Manager by taking the parameter `ibmim` in the play.

## Module Summary
| Module | Description |
|:-------|:------------|
| ibmim.py | Installs and uninstalls IBM Installation Manager. |
| imwas.py | Install and uninstalls WebSphere Application Server including Liberty Profile. Uses Installation manager. Assumes Installation Manager is already present. |
| profile_dmgr.py | Creates or removes a WebSphere Application Server Deployment Manager profile. Requires a Network Deployment installation. |
| profile_nodeagent.py |Creates or removes a WebSphere Application Server Node Agent profile. Requires a Network Deployment installation. |
| profile_liberty.py | Creates or removes a Liberty Profile server runtime |
| server.py | Start or stops a WebSphere Application Server |
| liberty_server.py | Start or stops a Liberty Profile server |


## Modules
### ibmim.py
This module installs or uninstalls IBM Installation Manager.
#### Options
| Parameter | Required | Default | Choices | Comments |
|:---------|:--------|:---------|:---------|:---------|
| state | false | N/A | present, absent | present=install, absent=uninstall |
| src | false | N/A | N/A | Path to installation files for Installation Manager |
| dest | false | N/A | /opt/IBM/InstallationManager | Path to desired installation directory of Installation Manager |
| logdir | false | N/A | /tmp | Path and file name of installation log file |
#### Example
```
# Install:
ibmim: state=present src=/some/dir/install/
# Uninstall
ibmim: state=absent dest=/opt/IBM/InstallationManager
```

### ibmwas.py
This module installs or uninstalls IBM WebSphere products using Installation Manager.
#### Options
| Parameter | Required | Default | Choices | Comments |
|:---------|:--------|:---------|:---------|:---------|
| state | false | present | present, absent | present=install,absent=uninstall |
| ibmim | false | /opt/IBM/InstallationManager | N/A | Path to installation directory of Installation Manager |
| dest | true | N/A | N/A | Path to destination installation directory |
| im_shared | false | N/A | N/A | Path to Installation Manager shared resources folder |
| repo | false | N/A | N/A | URL or path to the installation repository used by Installation Manager to install WebSphere products |
| offering | true | N/A | N/A | Name of the offering which you want to install |
#### Example
```
# Install:
ibmwas: state=present ibmim=/opt/IBM/InstallationManager/ dest=/usr/local/WebSphere/AppServer im_shared=/usr/local/WebSphere/IMShared repo=http://example.com/was-repo/ offering=com.ibm.websphere.ND.v85
# Uninstall:
ibmwas: state=absent ibmim=/opt/IBM/InstallationManager dest=/usr/local/WebSphere/AppServer/
```

### profile_dmgr.py
This module creates or removes a WebSphere Application Server Deployment Manager profile. Requires a Network Deployment installation.
#### Options
| Parameter | Required | Default | Choices | Comments |
|:---------|:--------|:---------|:---------|:---------|
| state | true | present | present,absent | present=create,absent=remove |
| wasdir | true | N/A | N/A | Path to installation location of WAS |
| name | true | N/A | N/A | Name of the profile |
| cell_name | true | N/A | N/A | Name of the cell |
| host_name | true | N/A | N/A | Host Name |
| node_name | true | N/A | N/A | Node name of this profile |
| username | true | N/A | N/A | Administrative user name |
| password | true | N/A | N/A | Administrative user password |
#### Example
```
# Create:
profile_dmgr: state=present wasdir=/usr/local/WebSphere/AppServer/ name=dmgr cell_name=devCell host_name=localhost node_name=devcell-dmgr username=admin password=allyourbasearebelongtous
# Remove:
profile_dmgr: state=absent wasdir=/usr/local/WebSphere/AppServer/ name=dmgr
```

### profile_nodeagent.py
This module creates or removes a WebSphere Application Server Node Agent profile. Requires a Network Deployment installation.
#### Options
| Parameter | Required | Default | Choices | Comments |
|:---------|:--------|:---------|:---------|:---------|
| state | true | present | present,absent | present=create,absent=remove |
| wasdir | true | N/A | N/A | Path to installation location of WAS |
| name | true | N/A | N/A | Name of the profile |
| cell_name | true | N/A | N/A | Name of the cell |
| host_name | true | N/A | N/A | Host Name |
| node_name | true | N/A | N/A | Node name of this profile |
| username | true | N/A | N/A | Administrative user name of the deployment manager |
| password | true | N/A | N/A | Administrative user password of the deployment manager |
| dmgr_host | true | N/A | N/A | Host name of the Deployment Manager |
| dmgr_port | true | N/A | N/A | SOAP port number of the Deployment Manager |
| federate | false | N/A | N/A | Wether the node should be federated to a cell. If true, cell name cannot be the same as the cell name of the deployment manager. |
#### Example
```
# Create
profile_nodeagent: state=present wasdir=/usr/local/WebSphere/AppServer/ name=nodeagent cell_name=devCellTmp host_name=localhost node_name=devcell-node1 username=admin password=allyourbasearebelongtous dmgr_host=localhost dmgr_port=8879 federate=true
# Remove:
profile_dmgr: state=absent wasdir=/usr/local/WebSphere/AppServer/ name=nodeagent
```

### server.py
This module start or stops a WebSphere Application Server
#### Options
| Parameter | Required | Default | Choices | Comments |
|:---------|:--------|:---------|:---------|:---------|
| state | true | started | started, stopped | N/A |
| name | true | N/A | N/A | Name of the app server |
| wasdir | true | N/A | N/A | Path to binary files of the application server |
| username | true | N/A | N/A | Administrative user name |
| password | true | N/A | N/A | Administrative user password |
#### Example
```
# Start:
server: state=started wasdir=/usr/local/WebSphere/AppServer/ name=my-server-01
# Stop:
server: state=stopped wasdir=/usr/local/WebSphere/AppServer/ name=my-server-01
```
### liberty_server.py
This module start or stops a Liberty Profile server
#### Options
| Parameter | Required | Default | Choices | Comments |
|:---------|:--------|:---------|:---------|:---------|
| state | true | started | started, stopped | N/A |
| name | true | N/A | N/A | Name of the app server |
| libertydir | true | N/A | N/A | Path to binary files of the application server |
#### Example
```
# Start:
liberty_server: state=started libertydir=/usr/local/WebSphere/Liberty/ name=my-server-01
# Stop:
liberty_server: state=stopped libertydir=/usr/local/WebSphere/Liberty/ name=my-server-01
```

### profile_liberty.py
This module creates or removes a Liberty Profile server runtime
#### Options
| Parameter | Required | Default | Choices | Comments |
|:---------|:--------|:---------|:---------|:---------|
| state | true | present | present,absent | present=create,absent=remove |
| libertydir | true | N/A | N/A | Path to install location of Liberty Profile binaries |
| name | true | N/A | N/A | Name of the server which is to be created/removed |
#### Example
```
# Create:
profile_liberty: state=present libertydir=/usr/local/WebSphere/Liberty/ name=server01
# Remove
profile_liberty: state=absent libertydir=/usr/local/WebSphere/Liberty/ name=server01
```
