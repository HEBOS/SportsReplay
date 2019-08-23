import cv2
import multiprocessing as mp
import time
import psutil
import gc
from pympler.tracker import SummaryTracker
from mem_top import mem_top

mp.set_start_method('forkserver')

tracker = SummaryTracker()

before = psutil.virtual_memory()
image = cv2.imread(
    '/home/sportsreplay/GitHub/sports-replay-hrvoje/ActivityDetector/SampleImages/frame_1564827634_0001.jpg')
q = mp.Queue()

for i in range(500):
    q.put(image)

q.put(None)

while True:
    if not q.empty():
        some_image = q.get()
        if some_image is None:
            del some_image
            break
        del some_image

del image
del q

cv2.waitKey(1)
cv2.destroyAllWindows()
for i in range(1, 5):
    cv2.waitKey(1)

n = gc.collect()
print("Waiting for garbage collector to reclaim the memory.")
after = psutil.virtual_memory()
print("Memory leaked by {} bytes.".format(after.used - before.used))

print('Unreachable objects:', n)
print('Remaining Garbage:', gc.garbage)

print("Final gc.collect()")

del before
del after
n = gc.collect()

tracker.print_diff()

print(mem_top())

print("Finished.")
