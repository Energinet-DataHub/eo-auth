# Setup development environment for VSCode


## Devcontainer
This project includes a [development container](https://code.visualstudio.com/docs/remote/containers) configuration, which lets you run the full-featured development environment inside a [Docker container](https://docker.com/). This is the fastest and easiest solution to get a development environment up and running.

### System Requirements
- Docker running on local machine
- VSCode Extenstion: [Remote Development](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack)

### Getting started

When system requirements are met, open the codeproject within VSCode. Upon opening the project, VSCode might prombt you that this project contains a devcontainer and if you wanna open this, press yes. If not open VSCode [Command Palette](https://code.visualstudio.com/docs/getstarted/userinterface#_command-palette) using `Ctrl + Shift + P` or `F1` then enter:

    > Remote-Containers: Rebuild Container


You should then have a full-featured development environment up and running.
