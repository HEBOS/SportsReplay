import cv2


#input_pipeline = "filesrc location='/home/sportsreplay/GitHub/sports-replay-hrvoje/videos/2.mp4' num-buffers=1000 ! 'video/x-h264,width=(int)1280,height=(int)720,framerate=(fraction)25/1,format=(string)byte-stream' ! queue ! nvvidconv ! 'video/x-raw(memory:NVMM)' ! queue ! nvjpegenc ! fakesink -v -e"

input_pipeline = "filesrc location=/home/sportsreplay/GitHub/sports-replay-hrvoje/videos/2.mp4 " \
                          "! h264parse " \
                          "! nv_omx_h264dec " \
                          "! filesink"

input_pipeline = "filesrc location=/home/sportsreplay/GitHub/sports-replay-hrvoje/videos/2.mp4 " \
                 "! image/jpeg,width=1280,height=720,framerate=25/1 " \
                 "! jpegparse " \
                 "! jpegdec " \
                 "! videoconvert " \
                 "! videoscale " \
                 "! appsink"

input_pipeline = "filesrc location=/home/sportsreplay/GitHub/sports-replay-hrvoje/videos/2.mp4 " \
                 "! qtdemux name=demux " \
                 "! h264parse " \
                 "! omxh264dec ! " \
                 "autovideosink "

capture = cv2.VideoCapture(input_pipeline, cv2.CAP_GSTREAMER)

print("isopen={}".format(capture.isOpened()))
print(input_pipeline)
grabbed, frame = capture.read()
print(grabbed)
if grabbed:
    cv2.imwrite("x.jpg", frame)
