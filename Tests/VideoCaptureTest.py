import cv2
import psutil

source = '/home/sportsreplay/GitHub/sports-replay-hrvoje/ActivityDetector/SampleImages/frame_1564827634_0001.jpg'
capture = cv2.VideoCapture(source)
capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
capture.set(cv2.CAP_PROP_FPS, 25)
capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
capture.set(cv2.CAP_PROP_EXPOSURE, -8)

memory_start = psutil.virtual_memory()
memory_snapshot = memory_start

frame = None
counter = 0
successful_grab_counter = 0
while capture.isOpened():
    counter += 1
    if counter % 3000 == 0:
        memory_current = psutil.virtual_memory()
        print("memory delta cumulative: " + str(memory_current.used - memory_start.used))
        print("memory delta since last snapshot: " + str(memory_current.used - memory_snapshot.used))
        print("this is iteration number: " + str(counter) + ". Successfully grabbed this many frames: " + str(successful_grab_counter))
        memory_snapshot = memory_current
    grabbed = capture.grab()
    if grabbed:
        ref, frame = capture.retrieve()
        # cv2.imshow('frame', frame)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break
        successful_grab_counter += 1

capture.release()
cv2.destroyAllWindows()
