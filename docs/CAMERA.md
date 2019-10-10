# Configuring the Camera

1. Connect the camera with ethernet cable.

2. Open Internet Explorer (it doesn't work with other browsers correctly)

3. Open Configuration, and change:

    Basic Information
 
    - Device Name to state sports-replay-camera-X, where X is the next ID of the camera, as documented in [Devices Google sheet](https://docs.google.com/spreadsheets/d/1Tg_gxh4OfoJmMWTyH1NMfoTsNLtMI4H4KceRg6mj3fs/edit#gid=0)
    
    - Device No. to state X, where X is the next ID of the camera, as documented in [Devices Google sheet](https://docs.google.com/spreadsheets/d/1Tg_gxh4OfoJmMWTyH1NMfoTsNLtMI4H4KceRg6mj3fs/edit#gid=0)
    
    Image Settings
    - Un-tick all options under OSD settings
    
    - Turn on Smart Supplement Light
    
    - Set Exposure Settings to 1/250
    
    Network WLAN
    
    - Set IP address to your preference, as documented in [Devices Google sheet](https://docs.google.com/spreadsheets/d/1Tg_gxh4OfoJmMWTyH1NMfoTsNLtMI4H4KceRg6mj3fs/edit#gid=0)
    
    - Set Default Gateway to point to IP address of the router, as documented in [Devices Google sheet](https://docs.google.com/spreadsheets/d/1Tg_gxh4OfoJmMWTyH1NMfoTsNLtMI4H4KceRg6mj3fs/edit#gid=0)
    
    Ports
  
    - Enable RTSP protocol on port 554
    
    System - User Management
    
    - Add "sportsreplay" user for RTSP authentication, use the same password, as for Jetson, and Raspberry devices at that business client.
    
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
