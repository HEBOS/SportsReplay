import cv2
import time

source_path = "filesrc location={location} latency=2000 " \
                              "! qtdemux " \
                              "! queue " \
                              "! h264parse " \
                              "! nvv4l2decoder " \
                              "! capsfilter caps='video/x-raw(memory:NVMM),width={width},height=(int){height},format=(string)NV12, framerate=(fraction){fps}/1'" \
                              "! nvvidconv " \
                              "! video/x-raw,format=BGRx " \
                              "! videoconvert " \
                              "! videorate skip-to-first=1 qos=0 average-period=0000000000 max-rate={fps} " \
                              "! queue " \
                              "! appsink".format(location="/home/sportsreplay/GitHub/sports-replay-local/videos/test-video-1.mp4",
                                                 fps=16,
                                                 width=1280,
                                                 height=720,
                                                 user="sportsreplay",
                                                 password="PASSWORD_HERE")

output_pipeline = "appsrc " \
                  "! capsfilter caps='video/x-raw,format=I420,framerate={fps}/1' " \
                  "! videoconvert " \
                  "! capsfilter caps='video/x-raw,format=(string)BGRx,interpolation-method=0' " \
                  "! nvvideoconvert " \
                  "! capsfilter caps='video/x-raw(memory:NVMM)' " \
                  "! nvv4l2h264enc " \
                  "! h264parse " \
                  "! qtmux " \
                  "! filesink location=/home/sportsreplay/tmp/video-making/00001-002-2019-09-21-22-49.mp4v".format(width=1280,
                                                                                                                   height=720,
                                                                                                                   fps=25)


print("gst-launch-1.0 " + source_path)
print("gst-launch-1.0 " + output_pipeline)

print("Starting video capture...")
capture = cv2.VideoCapture(source_path, cv2.CAP_GSTREAMER)
print("Starting video writer...")
writer = None

print("isopen={}".format(capture.isOpened()))
i = 0
grabbed = capture.grab()
start_time = time.time()
while time.time() - start_time < 10:
    grabbed = capture.grab()

    if grabbed:
        i += 1
        ref, frame = capture.retrieve()
        if writer is None:
            writer = cv2.VideoWriter(output_pipeline,
                            cv2.VideoWriter_fourcc(*'mp4v'),
                            25,
                            (1280, 720),
                            True)
        writer.write(frame)
        if i % 10 == 0:
            cv2.imwrite("out.png", frame)

print("Uhvaćeno {} frame-ova".format(i))

capture.release()
writer.release()
