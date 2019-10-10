# SportsReplay

## Cloning this repository
`mkdir $HOME/GitHub`

`cd $HOME/GitHub`

`git clone https://github.com/HEBOS/SportsReplay.git sports-replay`

## Naming Convention

_All device attributes should be saved to the following Google Sheet:_
 https://docs.google.com/spreadsheets/d/1Tg_gxh4OfoJmMWTyH1NMfoTsNLtMI4H4KceRg6mj3fs/edit#gid=0 

-   Setup WiFi Network SSID to sports-replay-wifi-X, where X is the next available Sports Replay WiFi router number in client's building
-   Setup Jetson Nano host name to sports-replay-ai-X where X is next available Jetson Nano machine ID.
-	Setup Raspbery Pi host name to sports-replay-pi-X where X is next available Pi machine ID.
-	Create unique complex password using password generator https://passwordsgenerator.net. Note that only "Include Lowercase Characters" and "Exclude Similar Characters" should be selected. Also make sure to put the dot at the end of the password, as Raspberry requires at least one special character.

## Setting up the Router

    1. Set up the router, assigning SSID, according to naming convention defined above.   
    2. Enable only network 2G, or 5G, whichever is supported by installed cameras.
    3. Define DHCP reservations, and make sure to add that information to Devices Google sheet found above.
    4. Restart the router

## Setting up Jetson Nano

### OS Installation
    Download JetPack from here https://developer.nvidia.com/embedded/jetpack

    Burn SD card using downloaded image above using Balena Etcher which can be downloaded from https://www.balena.io/etcher

    Follow the instructions defined in the following article https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit#write.

#### Naming Convention
 

### Creating a swap file
`sudo bash $HOME/GitHub/sports-replay/Bash-Scripts/create_swap_file.sh`

_Note that Jetson will be automatically rebooted._

### Preventing SSH timeout on Jetson
`sudo vi /etc/ssh/sshd_config`

##### Change the following values:
    - ClientAliveInterval 120
    - ClientAliveCountMax 720

_Make sure you reboot Jetson now. Otherwise it will still use the same setting._

### Disabling Jetson Nano GUI mode
`sudo systemctl set-default multi-user.target`

_Make sure you reboot Jetson now. Otherwise GUI will still be on._

_If you need to enable it again, run:_

`sudo systemctl set-default graphical.target`

_If you want to start gui, while it is currently disabled, run:_

`sudo systemctl start gdm3.service`

### Putting Jetson in 10w mode
`sudo bash $HOME/GitHub/sports-replay/Bash-Scripts/turn-10w-jetson-on.sh`

### Installing OpenCV 3.0 (the prerequisite)
`sudo apt-get install python3-opencv`

### Installing OpenCV 4.0
`cd $HOME/GitHub`

`sudo bash $HOME/GitHub/sports-replay/Bash-Scripts/install_opencv4.sh`

    From this point, you can disconnect the monitor, and access your device using SSH.

### Setting up the Tunneling

#### Server - Setup the Prerequisites on VPS (Already Done)
`vi /etc/ssh/sshd_config`

_Change the following setting:_

`PermitRootLogin without-password`

#### Remote Computer - Copying the Public Key
`ssh-copy-id -i ~/.ssh/id_rsa.pub root@78.46.214.162`

_If there is no key, run the following command, and after that repeat the previous step_

`ssh-keygen -o`

#### Hetzer Console - Adding Your Key
    Get your SSH key using `vi ~/.ssh/id_rsa.pub` and copy/paste the code as a new SSH key in Hetzer console `https://console.hetzner.cloud/projects/297870/access/sshkeys`

#### Remote Computer - Install tmux
`apt install tmux`

#### Remote Computer - Creating a Tunnel
`/usr/bin/tmux new-session -s tunneling -d  ssh -nN -R XXXX:localhost:22 root@78.46.214.162`

_Replace XXXX with the next available VPS port dedicated to tunelling. Also make sure to update the devices documentation with the port assigned._ 

#### Remote Computer - Create the Startup Script
`sudo vi /etc/init.d/create_tunnel.sh`

_Paste the above command for creating a tunnel into the script._

`chmod +x /etc/init.d/create_tunnel.sh`

#### Connecting to Remote Computer from Any Computer
`ssh sportsreplay@78.46.214.162 -p XXXX`

_Replace XXXX with previously assigned VPS port._


## Setting up Raspberry PI

### OS Installation
    1. Download Raspbian OS from here https://www.raspberrypi.org/downloads/raspbian/
    2. Burn SD card using downloaded image above using Balena Etcher which can be downloaded from https://www.balena.io/etcher
    3. Put the card into Raspbery device, and turn it on. Follow the instructions, and respect naming convention defined above.

### Enabling SSH service

    1. Launch Raspberry Pi Configuration from the Preferences menu
    2. Navigate to the Interfaces tab
    3. Select Enabled next to SSH
    4. Click OK
    5. Now you can disconnect the monitor, and access your device using SSH

### Performing OS upgrade

`sudo apt-get update`

`sudo apt update`

`sudo apt-get upgrade`

### Adding AI device address to Raspberry hosts file
`sudo nano /etc/hosts`
    
    192.168.0.xxx	sports-replay-ai-Y 
    
    _where xxx is, as defined in router setup explained below, and Y is, as defined during Jetson Nano device setup_
    
### Installing the FTP server on Raspberry PI

`sudo apt-get update`

`sudo apt-get install vsftpd`

`sudo nano /etc/vsftpd.conf`

    Add/uncomment lines in config file:

    anonymous_enable=NO
    local_enable=YES
    write_enable=YES
    local_umask=022
    chroot_local_user=YES
    user_sub_token=$USER
    local_root=/home/$USER/FTP

#### Create FTP directory, and restart FTP service

`mkdir /home/pi/FTP`

`sudo service vsftpd restart`
