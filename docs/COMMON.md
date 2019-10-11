# Common Instructions

## Naming Convention

All device attributes should be saved to the [Devices Google sheet](https://docs.google.com/spreadsheets/d/1Tg_gxh4OfoJmMWTyH1NMfoTsNLtMI4H4KceRg6mj3fs/edit#gid=0).
  

-   Set WiFi Network SSID to __sports-replay-wifi-X__, where X is the next available Sports Replay WiFi router number in client's building
-   Set Jetson Nano host name to __sports-replay-ai-X__ where X is next available Jetson Nano machine ID.
-	Set Raspbery Pi host name to __sports-replay-pi-X__ where X is next available Pi machine ID.
-	Create unique complex password using [password generator](https://passwordsgenerator.net). Note that only "Include Lowercase Characters" and "Exclude Similar Characters" should be selected. Also make sure to put the __dot at the end of the password__, as Raspberry requires at least one special character.

## Setting up The Tunneling

### Login as "root" User

`sudo su`

Create The Public Key

`ssh-keygen -o`

    Make sure to press ENTER 3 times.
    Do not provide any passphrase, otherwise you won't be getting passwordless login.

### Remote Computer - Copying The Public Key
`ssh-copy-id -i ~/.ssh/id_rsa.pub root@78.46.214.162`

    You will need to provide root password for VPS.

### Install "autossh" 
`sudo apt install autossh`

### Creating The Tunneling Service

Raspberry Pi

`sudo nano /etc/systemd/system/autossh-tunnel.service `

Jetson

`sudo vi /etc/systemd/system/autossh-tunnel.service `

Paste the following content in it (replace __XXXX__ with the next available VPS port dedicated to tunneling).

    [Unit]
    Description=AutoSSH tunnel service on port 22
    After=network.target
    
    [Service]
    Environment="AUTOSSH_GATETIME=0"
    ExecStart=/usr/bin/autossh -M 0 -o "ServerAliveInterval 30" -o "ServerAliveCountMax 3" -nN -R XXXX:localhost:22 root@78.46.214.162
    
    [Install]
    WantedBy=multi-user.target

### Starting The Tunneling Service

`sudo systemctl start autossh-tunnel.service`


### Enabling The Tunneling Service to Run on Startup

`sudo systemctl enable autossh-tunnel.service`

Reboot

`sudo reboot`


### Testing on VPS If The Port Is Opened 

Open a separate terminal and use the following commands.

`ssh root@78.46.214.162`

`netstat -tulpn | grep LISTEN`

### Connecting to The Remote Computer from Any Computer

For Jetson (replace __XXXX with__ previously assigned VPS port.)

`ssh sportsreplay@78.46.214.162 -p XXXX`

For Raspberry Pi (replace __XXXX with__ previously assigned VPS port.)

`ssh pi@78.46.214.162 -p XXXX`


## Preventing SSH to Timeout
`sudo vi /etc/ssh/sshd_config`

### Change the following values:
    - ClientAliveInterval 120
    - ClientAliveCountMax 720

Make sure you reboot the device now. Otherwise it will still use the same setting.

## Disabling Linux GUI mode
`sudo systemctl set-default multi-user.target`

Make sure you reboot the device now. Otherwise GUI will still be on.

If you need to enable it again, run:

`sudo systemctl set-default graphical.target`

If you want to start gui, while it is currently disabled, run:

`sudo systemctl start gdm3.service`
