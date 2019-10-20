# Intermezzo

## Creating
`ffmpeg -loop 1 -i Intermezzo.png -c:v libx264 -t 15 -pix_fmt yuv420p -vf scale=1280:720 Intermezzo.mp4`

## Testing
` /usr/bin/omxplayer --win 0,0,1280,720 --display 7 --adev hdmi Intermezzo.mp4`

