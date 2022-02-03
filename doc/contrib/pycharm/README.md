# Setup development environment for PyCharm

# Install pipenv PyCharm

To install pipenv local to use in PyCharm, the following has to be done:

- [ ] Install python for Windows
- [ ] Install  Microsoft C++ Build Tools
- [ ] Install pipenv for Windows
- [ ] Configure a Pipenv environment
- [ ] Setup Configuration in PyCharm
 
---
## Install python for Windows

The Fenris project uses python 3.8.10

Link:  https://www.python.org/downloads/release/python-3810/

Remember to mark the "Add Python to enviroment variables"

Before installing the `pipenv` tool, you need to make sure that Python and `pip` are installed on your computer.

First, open the Command Prompt or Windows Powershell and type the following command.

```
python -V
```

Note that the letter `V` in the `-V` is uppercase. If you see the Python version like the following:

```
Python 3.8.5
```

…then you already have Python installed on your computer. Otherwise, you need to [install Python](https://www.pythontutorial.net/getting-started/install-python/) first.

Second, use the following command to check if you have the `pip` tool on your computer:

```
pip -V
```

It’ll return something like this:

```
pip 20.2.4 from C:\Users\<username>\AppData\Roaming\Python\Python38\site-packages\pip (python 3.8)
``` 

---
## Install  Microsoft C++ Build Tools

Microsoft C++ Build Tools is required to run the serpyco package in PyCharm

Link to Tools for Visual Studio 2022

https://visualstudio.microsoft.com/downloads/

or direct link;

https://aka.ms/vs/17/release/vs_BuildTools.exe

In the installation, Windows 10 SDK is required, however, problems can occur if the others default are not choosen.  

---
## Install pipenv for Windows
Link to the tool;
https://www.pythontutorial.net/python-basics/install-pipenv-windows/


## Install pipenv 

First, use the following command to install `pipenv` tool:

```
pip install pipenv
``` 

Second, replace your `<username>` in the following paths and add them to the `PATH` environment variable:

```
c:\Users\<username>\AppData\Roaming\Python\Python38\Site-Packages
C:\Users\<username>\AppData\Roaming\Python\Python38\Scripts
```

It’s important to notice that after changing the `PATH` environment variable, you need to close the Command Prompt and reopen it.

Third, type the following command to check if the `pipenv` installed correctly:

```
pipenv --version
```

If it shows the following output, then you’ve successfully installed the `pipenv` tool successfully.

```
Usage: pipenv [OPTIONS] COMMAND [ARGS]...
```

However, if you see the following message:

```
pipenv shell 'pipenv' is not recognized as an internal or external command, operable program or batch file.
```

Then you should go back and check if you have already added the paths to the `PATH` environment variable.

---

## Configure a Pipenv environment
Afterwards the environment must be configured in PyCharm which are explained how to do here:

https://www.jetbrains.com/help/pycharm/pipenv.html#pipenv-existing-project

---
### Install the pipenv from the pipfile
Then the pipenv needs to install the packages from the pipfile:

```
pipenv install
```

and sync the versions(may not be needed):

```
pipenv sync --dev
```

---
# Setup Configuration in PyCharm

Mark directory "src" and "test" as root for the source and test folder by right-clicking on the folder and select "Mark directory as"  

To run the API and the tests in PyCharm. The "Run/Debug Configuration" must be set as the following :

#### auth API 
In Run/Debug Configuration 

-> add new configuration and select Python

-> change "Script path" to "Module name" and set "auth_api" as the name

-> make sure that the "Python interpreter" is the Python 3.8(eo-auth-<pipenv>) 

-> set the "Working directory" to the "<folderpath>\eo-auth\src" folder 


#### Pytest 
In Run/Debug Configuration 

-> add new configuration and select pytest

-> set "Script path" to "<folderpath>/eo-auth/tests"

-> make sure that the "Python interpreter" is the Python 3.8(eo-auth-<pipenv>) 

-> set "Working directory" to the "<folderpath>\eo-auth\src" folder 


---
# Known errors
##### pypiwin32  was not installed in pipenv
docker.errors.DockerException: Install pypiwin32 package to enable npipe:// support

```
Solution:
Run the following command in PyCharm termial:
	pip install pypiwin32
```

---

##### Docker problems in Windows

While the tests are running in PyCharm, docker desktop might not be found due to  a name "localnpipe"

To fix this go to: 
External liberaties 
\.virtualenvs\eo-auth-<pipenv>\Lib\site-packages\docker\api\client.py

At line 168 change

```
self.base_url = 'http+docker://localnpipe'  
```
To:
```
self.base_url = 'http+docker://localhost'
```

The following link discuess the issue 
https://github.com/testcontainers/testcontainers-python/issues/108


---

##### ModuleNotFoundError: No module named 'atomicwrites'

pipenv install atomicwrites

---
