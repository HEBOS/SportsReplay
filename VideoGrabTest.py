import cv2

input_pipeline = "filesrc location=/home/sportsreplay/GitHub/sports-replay-hrvoje/videos/test-video-2.mp4 " \
                  "! qtdemux name=demux demux.video_0 " \
                  "! queue " \
                  "! h264parse " \
                  "! omxh264dec " \
                  "! nvvidconv " \
                  "! video/x-raw,format=RGBA," \
                  "width=1280,height=720,framerate=25/1 " \
                  "! videoconvert " \
                  "! appsink "

capture = cv2.VideoCapture(input_pipeline, cv2.CAP_GSTREAMER)

print("isopen={}".format(capture.isOpened()))
print(input_pipeline)

grabbed = capture.grab()
print(grabbed)
if grabbed:
    ref, frame = capture.retrieve(flag=0)
    cv2.imwrite("x.jpg", frame)

    output_pipeline = "appsrc " \
                      "! autovideoconvert " \
                      "! video/x-raw,width=1280,height=720,format=I420,framerate=25/1 " \
                      "! omxh264enc " \
                      "! video/x-h264,stream-format=byte-stream " \
                      "! h264parse " \
                      "! matroskamux " \
                      "! filesink location=x.mp4v "

    print(output_pipeline)
    writer = cv2.VideoWriter(output_pipeline,
                             cv2.VideoWriter_fourcc(*'mp4v'),
                             25, (1280, 720), True)

    for i in (0, 100):
        writer.write(frame)

    writer.release()
capture.release()
