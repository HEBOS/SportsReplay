import cv2
import multiprocessing as mp
import time
import psutil
import gc
from pympler.tracker import SummaryTracker
from mem_top import mem_top

# mp.set_start_method('forkserver')

tracker = SummaryTracker()

before = psutil.virtual_memory()
image = cv2.imread(
    '/home/sportsreplay/GitHub/sports-replay-hrvoje/ActivityDetector/SampleImages/frame_1564827634_0001.jpg')
# image = "bla"
q = mp.Queue()
foo = None


def fill_queue(q):
    for i in range(500):
        q.put(image)

# q.put(None)


while True:
    if not q.qsize() == 0:
        print(q.qsize())
        q.get()
    else:
        # print("filling queue with 500 images")
        fill_queue(q)

# cv2.waitKey(1)
# cv2.destroyAllWindows()
# for i in range(1, 5):
#     cv2.waitKey(1)

n = gc.collect()
print("Waiting for garbage collector to reclaim the memory.")
after = psutil.virtual_memory()
print("Memory leaked by {} bytes.".format(after.used - before.used))

print('Unreachable objects:', n)
print('Remaining Garbage:', gc.garbage)

print("Final gc.collect()")

before = None
after = None
n = gc.collect()

tracker.print_diff()

print(mem_top())

print("Finished.")
