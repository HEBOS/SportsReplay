import cv2

input_pipeline = "filesrc location=/home/sportsreplay/GitHub/sports-replay-hrvoje/videos/test-video-2.mp4 " \
                 "! qtdemux " \
                 "! h264parse " \
                 "! omxh264dec " \
                 "! nvvidconv " \
                 "! video/x-raw,format=RGBA,width={width},height={height},framerate={fps}/1 " \
                 "! videorate max-rate={fps} " \
                 "! autovideoconvert " \
                 "! appsink "

input_pipeline = "filesrc location=/home/sportsreplay/GitHub/sports-replay-hrvoje/videos/test-video-2.mp4 ! qtdemux ! h264parse ! omxh264dec ! nvvidconv ! video/x-raw(memory: NVMM),format=RGBA ! videoconvert ! appsink -vvv"

capture = cv2.VideoCapture(input_pipeline, cv2.CAP_GSTREAMER)

print("isopen={}".format(capture.isOpened()))
print(input_pipeline)

grabbed, frame = capture.read()
print(grabbed)
if grabbed:
    cv2.imwrite("x.jpg", frame)
