# Sports Replay - Common Instructions

## Naming Convention

_All device attributes should be saved to the following Google Sheet:_
 https://docs.google.com/spreadsheets/d/1Tg_gxh4OfoJmMWTyH1NMfoTsNLtMI4H4KceRg6mj3fs/edit#gid=0 

-   Setup WiFi Network SSID to sports-replay-wifi-X, where X is the next available Sports Replay WiFi router number in client's building
-   Setup Jetson Nano host name to sports-replay-ai-X where X is next available Jetson Nano machine ID.
-	Setup Raspbery Pi host name to sports-replay-pi-X where X is next available Pi machine ID.
-	Create unique complex password using password generator https://passwordsgenerator.net. Note that only "Include Lowercase Characters" and "Exclude Similar Characters" should be selected. Also make sure to put the dot at the end of the password, as Raspberry requires at least one special character.

### Setting up the Tunneling

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

### Preventing SSH timeout
`sudo vi /etc/ssh/sshd_config`

##### Change the following values:
    - ClientAliveInterval 120
    - ClientAliveCountMax 720

_Make sure you reboot the device now. Otherwise it will still use the same setting._

### Disabling Linux GUI mode
`sudo systemctl set-default multi-user.target`

_Make sure you reboot the device now. Otherwise GUI will still be on._

_If you need to enable it again, run:_

`sudo systemctl set-default graphical.target`

_If you want to start gui, while it is currently disabled, run:_

`sudo systemctl start gdm3.service`
