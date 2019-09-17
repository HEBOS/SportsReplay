import cv2

input_pipeline = "rtspsrc location=rtsp://192.168.0.103:8080/h264_pcm.sdp latency=2000 " \
                  "! rtph264depay " \
                  "! capsfilter caps=video/x-h264,width=1280," \
                  "height=720,framerate=(fraction)25/1 " \
                  "! queue " \
                  "! h264parse " \
                  "! omxh264dec " \
                  "! nvvidconv " \
                  "! video/x-raw,format=RGBA " \
                  "! videoconvert " \
                  "! appsink"

capture = cv2.VideoCapture(input_pipeline, cv2.CAP_GSTREAMER)

print("isopen={}".format(capture.isOpened()))
print(input_pipeline)

grabbed = capture.grab()
print(grabbed)
if grabbed:
    print(grabbed)
    ref, frame = capture.retrieve(flag=0)
    cv2.imwrite("x.jpg", frame)

capture.release()
