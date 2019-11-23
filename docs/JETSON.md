# Configuring Jetson Nano

## OS Installation
Download JetPack from [here](https://developer.nvidia.com/embedded/jetpack).

Burn SD card using downloaded image above using Balena Etcher which can be downloaded from [here](https://www.balena.io/etcher).

Follow the instructions defined in the [following article](https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit#write).

# Installing Python Requirements
`sudo apt-get install python3-pip`

`sudo pip3 install -r requirements.txt`

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
`sudo vi /etc/hosts`

## Install FTP Client
`sudo apt install ftp`

## Setting up The Tunneling
Read instructions [here](COMMON.md).

## Installing Support for Shared Memory
Install Arrow using the following [instructions](https://tutorials.technology/tutorials/21-how-to-compile-and-install-arrow-from-source-code.html).

### Note:
Create symbolic links for aarch64 architecture (the stated instructions are for x86/x64).

`sudo ln -s /usr/lib/aarch64-linux-gnu/libboost_regex.a /usr/lib/aarch64-linux-gnu/libboost_regex-mt.a`

`sudo ln -s /usr/lib/aarch64-linux-gnu/libboost_system.a /usr/lib/aarch64-linux-gnu/libboost_system-mt.a`

`sudo ln -s /usr/lib/aarch64-linux-gnu/libboost_filesystem.a /usr/lib/aarch64-linux-gnu/libboost_filesystem-mt.a`


### Note about installing parket-cpp

Building parquet-cpp master is no longer supported.  Build from C++
  codebase in https://github.com/apache/arrow with -DARROW_PARQUET=ON
  

### Nota about using CMAKE to build Arrow

`cmake -DARROW_PLASMA=ON -DARROW_PYTHON=ON -DARROW_PARQUET=ON ..`

`cd $HOME/GitHub`

`git clone https://github.com/apache/arrow.git`

`cd arrow/cpp`

`mkdir release`

`cd release`

`cmake -DARROW_PLASMA=ON -DARROW_PYTHON=ON -DARROW_PARQUET=ON ..`

`make -j4`

`make install`

`pip install brain-plasma`