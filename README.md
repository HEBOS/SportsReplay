# SportsReplay

## Cloning this repository
`mkdir $HOME/GitHub`

`cd $HOME/GitHub`

`git clone https://github.com/HEBOS/SportsReplay.git sports-replay`

## Setting up Jetson Nano

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

### Setting up the Tunneling

#### Setup the Prerequisites on VPS (Already Done)
`vi /etc/ssh/sshd_config`

_Change the following setting:_

`PermitRootLogin without-password`

#### Copying the Public Key
`ssh-copy-id -i ~/.ssh/id_rsa.pub root@78.46.214.162`

_If there is no key, run the following command, and after that repeat the previous step_

`ssh-keygen -o`

#### Adding Your Key to Hetzer Console
Get your SSH key using `vi ~/.ssh/id_rsa.pub` and copy/paste the code as a new SSH key in Hetzer console `https://console.hetzner.cloud/projects/297870/access/sshkeys`

#### Install tmux
apt install tmux

#### Creating a Tunnel
`/usr/bin/tmux new-session -s tunneling -d  ssh -nN -R XXXX:localhost:22 root@78.46.214.162`

_Replace XXXX with the next available VPS port dedicated to tunelling. Also make sure to update the devices documentation with the port assigned._ 

#### Create the Startup Script
`sudo vi /etc/init.d/create_tunnel.sh`

_Paste the above command for creating a tunnel into the script._

`chmod +x /etc/init.d/create_tunnel.sh`

#### Connecting to Jetson or Raspberry from the Remote Computer
`ssh sportsreplay@78.46.214.162 -p XXXX`

_Replace XXXX with previously assigned VPS port._
