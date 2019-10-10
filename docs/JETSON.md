# Sports Replay - Configuring Jetson Nano

### OS Installation
Download JetPack from [here](https://developer.nvidia.com/embedded/jetpack).

Burn SD card using downloaded image above using Balena Etcher which can be downloaded from [here](https://www.balena.io/etcher).

Follow the instructions defined in the [following article](https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit#write).

## Cloning this repository
The cloning of this repository needs to be done into $HOME/GitHub/sports-replay folder, as described [here](../README.md).
 
### Creating a swap file
`sudo bash $HOME/GitHub/sports-replay/Bash-Scripts/create_swap_file.sh`

    Note that Jetson will be automatically rebooted.

### Preventing SSH timeout on Jetson
Read instructions [here](../README.md).

### Disabling Jetson Nano GUI mode
Read instructions [here](../README.md).

### Putting Jetson in 10w mode
`sudo bash $HOME/GitHub/sports-replay/Bash-Scripts/turn-10w-jetson-on.sh`

### Installing OpenCV 3.0 (the prerequisite)
`sudo apt-get install python3-opencv`

### Installing OpenCV 4.0
`cd $HOME/GitHub`

`sudo bash $HOME/GitHub/sports-replay/Bash-Scripts/install_opencv4.sh`

    From this point, you can disconnect the monitor, and access your device using SSH.

### Setting up the Tunneling
Read instructions [here](../README.md).

