# SportsReplay

##Cloning this repository
mkdir $HOME/GitHub

cd $HOME/GitHub

git clone https://github.com/HEBOS/SportsReplay.git sports-replay

##Setting up Jetson Nano

###Creating a swap file
sudo bash $HOME/GitHub/sports-replay/Bash-Scripts/create_swap_file.sh

###Preventing SSH timeout on Jetson
sudo vi /etc/ssh/sshd_config

#####Change the following values:
- ClientAliveInterval 120
- ClientAliveCountMax 720

###Disabling Jetson Nano GUI mode
sudo systemctl set-default multi-user.target

###Enabling Jetson Nano GUI mode
sudo systemctl set-default graphical.target

###Starting GUI from CLI mode
sudo systemctl start gdm3.service

###Putting Jetson in 10w mode
sudo bash $HOME/GitHub/sports-replay/Bash-Scripts/turn-10w-jetson-on.sh

###Installing OpenCV 3.0 (the prerequisite)
sudo apt-get install python3-opencv

###Installing OpenCV 4.0
sudo bash $HOME/GitHub/sports-replay/Bash-Scripts/install_opencv4.sh
