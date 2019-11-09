# Configuring Jetson Nano

## OS Installation
Download JetPack from [here](https://developer.nvidia.com/embedded/jetpack).

Burn SD card using downloaded image above using Balena Etcher which can be downloaded from [here](https://www.balena.io/etcher).

Follow the instructions defined in the [following article](https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit#write).

# Installing Python Requirements
`sudo apt-get install python3-pip`

`sudo pip install -r requirements.txt`

## Cloning This Repository
The cloning of this repository needs to be done into $HOME/GitHub/sports-replay folder, as described [here](../README.md).
 
## Creating a Swap File
`sudo bash $HOME/GitHub/sports-replay/Bash-Scripts/create_swap_file.sh`

    Note that Jetson will be automatically rebooted.

## Preventing SSH Timeout on Jetson
Read instructions [here](COMMON.md).

## Disabling Jetson Nano GUI mode
Read instructions [here](COMMON.md).

## Putting Jetson in 10w Mode
`sudo bash $HOME/GitHub/sports-replay/Bash-Scripts/turn-10w-jetson-on.sh`

## Installing OpenCV 3.0 (the prerequisite)
`sudo apt-get install python3-opencv`
    
    Make sure you reboot Jetson now.
    
## Installing OpenCV 4.0
`cd $HOME/GitHub`

`sudo bash $HOME/GitHub/sports-replay/Bash-Scripts/install_opencv4.sh`

    From this point, you can disconnect the monitor, and access your device using SSH.

## Add The Rasperry PI Address to Hosts File
`sudo /etc/hosts`

## Install FTP Client
`sudo apt install ftp`

## Setting up The Tunneling
Read instructions [here](COMMON.md).

