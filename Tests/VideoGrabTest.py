import cv2
import time

#input_pipeline = "rtsp://192.168.0.103:8080/h264_pcm.sdp"
input_pipeline = "rtspsrc location=rtsp://192.168.0.103:8080/h264_pcm.sdp latency=2000 " \
                 "! rtph264depay " \
                 "! video/x-h264,width=1280,height=720,framerate=25/1 " \
                 "! queue " \
                 "! h264parse " \
                 "! omxh264dec " \
                 "! video/x-raw,format=NV12,width={width},height={height},framerate={fps}/1 " \
                 "! videorate skip-to-first=1 qos=0 average-period=0000000000 " \
                 "! video/x-raw,width=1280,height=720,framerate=25/1 " \
                 "! videoconvert " \
                 "! video/x-raw,format=BGR " \
                 "! appsink"

output_pipeline = "appsrc " \
                  "! videoconvert " \
                  "! video/x-raw,width=1280,height=720,format=I420,framerate=25/1 " \
                  "! omxh264enc " \
                  "! h264parse " \
                  "! qtmux " \
                  "! filesink location=/home/sportsreplay/tmp/video-making/00001-002-2019-09-21-22-49.mp4v"

print("gst-launch-1.0 " + input_pipeline)
capture = cv2.VideoCapture(input_pipeline, cv2.CAP_GSTREAMER)
writer = cv2.VideoWriter(output_pipeline,
                                 cv2.VideoWriter_fourcc(*'mp4v'),
                                 25,
                                 (1280, 720),
                                 True)

print("isopen={}".format(capture.isOpened()))
i = 0
grabbed = capture.grab()
start_time = time.time()
while time.time() - start_time < 10:
    grabbed = capture.grab()

    if grabbed:
        i += 1
        ref, frame = capture.retrieve()
        writer.write(frame)

print("Uhvaćeno {} frame-ova".format(i))

capture.release()
writer.release()