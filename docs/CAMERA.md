# Configuring the Camera

1. Connect the camera with ethernet cable.

2. Open Internet Explorer (it doesn't work with other browsers correctly)

3. Open Configuration, and change:

    System Settings -> Basic Information
 
    - Device Name to state sr-camera-X, where X is the next ID of the camera, as documented in [Devices Google sheet](https://docs.google.com/spreadsheets/d/1Tg_gxh4OfoJmMWTyH1NMfoTsNLtMI4H4KceRg6mj3fs/edit?usp=sharing)
    
    - Device No. to state X, where X is the next ID of the camera, as documented in [Devices Google sheet](https://docs.google.com/spreadsheets/d/1Tg_gxh4OfoJmMWTyH1NMfoTsNLtMI4H4KceRg6mj3fs/edit?usp=sharing)
    
    System Settings -> Time Settings

    - Tick NTP, and set interval to 60 minutes
    
    Basic Settings -> NAT
    - Device Name to state sr-camera-X
        
    Network -> Basic Settings -> WLAN
    
    - Set IP address to your preference, as documented in [Devices Google sheet](https://docs.google.com/spreadsheets/d/1Tg_gxh4OfoJmMWTyH1NMfoTsNLtMI4H4KceRg6mj3fs/edit?usp=sharing)
    - Do not forget to add camera MAC address to the router reservation table, and assign ip address assigned above 
    - Set Default Gateway to point to IP address of the router, as documented in [Devices Google sheet](https://docs.google.com/spreadsheets/d/1Tg_gxh4OfoJmMWTyH1NMfoTsNLtMI4H4KceRg6mj3fs/edit?usp=sharing)
    - Set primary DNS to 8.8.8.8
    
    Network -> Advanced Network -> WiFi
    - Select WiFi network
    - Select security mode WPA2-personal
    - Select encryption type AES
    - Set password (key 1)
    - Un-tick Enable WPS
    
    Network -> Basic Settings -> Ports
  
    - Enable RTSP protocol on port 554
    
    System - User Management
    
    - Add "sportsreplay" user for RTSP authentication, and  make sure to put the same password to [Devices Google sheet](https://docs.google.com/spreadsheets/d/1Tg_gxh4OfoJmMWTyH1NMfoTsNLtMI4H4KceRg6mj3fs/edit?usp=sharing), and sports-replay.ini, as part of video setting in section __recorder__.
    
    Image Settings -> OSD Settings
    
    - Un-tick all options under OSD settings
    
    Image Settings -> Display Settings -> Day/Night switch
    
    - Set Day/Night Switch to Day 
    - Turn on Smart Supplement Light
    
    Image Settings -> Display Settings -> Exposure Settings
    
    - Set Exposure Settings to 1/250
    
    Video/Audio Settings
    
    - Resolution - 1280 x 720
    
    - Bitrate Type - Constant
    
    - Frame Rate - 25
    
    - Max. Bitrate - 2048
    
    - Video Encoding - H.264
    
    - H.264+ - OFF
    
    - I Frame interval - 10
    
    - SVC - Off
    
    - Smoothing - 75
