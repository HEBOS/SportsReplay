# SportsReplay

To be able to use fake video streams to do the testing, we need to use v4l2loopback utility.

Installing support for streaming mp4 file to dev/videoX:

sudo apt install v4l2loopback-dkms

sudo modprobe v4l2loopback devices=2


Removing v42loopback devices:

sudo modprobe -r v4l2loopback


Installing ffmpeg:

sudo apt install ffmpeg


Streaming mp4 as video file:

ffmpeg -r 25 -re -i 1.mp4 -map 0:v -input_format mjpeg -pix_fmt yuyv422 -f v4l2 /dev/video0

ffmpeg -r 25 -re -i 2.mp4 -map 0:v -input_format mjpeg -pix_fmt yuyv422 -f v4l2 /dev/video1
