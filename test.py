import numpy as np
import cv2

img = cv2.imread("out.jpg")
size = img.shape[:2]
channels = img.shape[2]
narr = img.tobytes()


print("Size: {}".format(size))
print("Channels: {}".format(channels))

with open("testout.jpg", 'wb') as f:
    f.write(narr)
    f.close()

with open("testout.jpg", 'rb') as f:
    img_bytes = f.read()
    f.close()
    modified_image = np.frombuffer(img_bytes, dtype=np.uint8)
    reshaped_image = modified_image.reshape(*size, channels)
    cv2.imwrite("testout2.jpg", reshaped_image)


