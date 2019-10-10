# Sports Replay - Configuring Raspberry Pi

### OS Installation
1. Download Raspbian OS from here https://www.raspberrypi.org/downloads/raspbian/
2. Burn SD card using downloaded image above using Balena Etcher which can be downloaded from https://www.balena.io/etcher
3. Put the card into Raspbery device, and turn it on. Follow the instructions, and respect naming convention defined above.

### Changing the Host Name
Give the name according to the [Naming Convention](../README.md).

`sudo nano /etc/hostname`

`sudo reboot`


### Enabling SSH service

 `sudo raspi-config` 

    1. Select Interfacing Options
    2. Navigate to and select SSH
    3. Choose Yes
    4. Select Ok
    5. Choose Finish

### Preventing SSH timeout on Raspberry
Read instructions [here](../README.md).

### Performing OS upgrade

`sudo apt-get update`

`sudo apt update`

`sudo apt-get upgrade`


### Adding Respective Jetson Nano Device Address to Raspberry Hosts File
`sudo nano /etc/hosts`
    
    192.168.0.xxx	sports-replay-ai-Y 
    
Where xxx is, as defined in router setup explained below, and Y is, as defined during [Jetson Nano](JETSON.md) device setup.
    
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

### Disabling Raspberry GUI mode
Full instructions can be found in [Disabling Linux GUI mode](../README.md) section.

### Setting up the Tunneling
Full instructions can be found in [Setting up the Tunneling](../README.md) section.
