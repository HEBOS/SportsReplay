# Configuring Raspberry Pi

### OS Installation
1. Download Raspbian OS from here https://www.raspberrypi.org/downloads/raspbian/
2. Burn SD card using downloaded image above using Balena Etcher which can be downloaded from https://www.balena.io/etcher
3. Put the card into Raspbery device, and turn it on. Follow the instructions, and respect naming convention defined [here](COMMON.md).
4. Make sure you select 5G WiFi during the OS installation

### After OS Installation
Open "Rasberry PI Configuration" screen

System tab:
	
- Hostname - Enter a new name according to Naming Conventions

- Auto-Login - Disable option

- Boot - To CLI

- Network at Boot - Wait for network

Interfaces tab:
	
- Set SSH to enabled

### Modifying the hosts file
`sudo nano /etc/hosts`
    
Add the following entry:

    192.168.0.xxx	sports-replay-ai-Y 
     
Where:
 - xxx us defined in router setup explained below
 - Y is the ID defined during [Jetson Nano](JETSON.md) device setup.

At this point, we need to run `sudo reboot` to apply the host name changes.

### Preventing SSH timeout on Raspberry
Read instructions [here](COMMON.md).

### Performing OS upgrade

`sudo apt-get update`

`sudo apt update`

`sudo apt-get upgrade`
    
### Installing the FTP server on Raspberry PI

`sudo apt-get update`

`sudo apt-get install vsftpd`

`sudo nano /etc/vsftpd.conf`

Add, uncomment, or amend lines in the config file:

Amend

    anonymous_enable=NO
    local_enable=YES
    write_enable=YES
    local_umask=022
    chroot_local_user=YES

Add

    user_sub_token=$USER
    local_root=/home/$USER/FTP

#### Create FTP directory, and restart FTP service

`mkdir /home/pi/FTP`

`sudo service vsftpd restart`

### Setting up the Tunneling
Full instructions can be found in [Setting up the Tunneling](../README.md) section.
