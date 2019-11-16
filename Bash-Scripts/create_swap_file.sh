#!/usr/bin/env bash
mkdir /home/sportsreplay/GitHub
cd /home/sportsreplay/GitHub
git clone https://github.com/JetsonHacksNano/installSwapfile
cd installSwapfile
sudo chmod +x installSwapfile.sh
./installSwapfile.sh
sudo reboot
