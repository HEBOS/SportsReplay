import cv2
import time

start = time.time()
image = cv2.imread('/home/sportsreplay/GitHub/sports-replay-hrvoje/ActivityDetector/SampleImages/frame_1564827634_0001.jpg')


output_pipeline = "appsrc ! nvjpegenc ! \"image/jpeg\" ! filesink location=videotestsrc-frame.jpg"

for i in range(25):
    #cv2.imwrite('/home/sportsreplay/tmp/' + str(i) + ".jpg", image)
    out = cv2.VideoWriter(output_pipeline, cv2.VideoWriter_fourcc(*'JPEG'), 1, (1280, 720))
    out.write(image)

end = time.time()

total_time = end - start
print(total_time)
