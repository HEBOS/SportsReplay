from Shared.LogoRenderer import LogoRenderer
import cv2
import os
import time

field = cv2.imread(os.path.join(os.getcwd(), "tmp/field.png"), cv2.IMREAD_COLOR)
logo_path = os.path.join(os.getcwd(), "Images/sports-replay-logo.png")
font_path = os.path.join(os.getcwd(), "Fonts/RobotoCondensed-Regular.ttf")
resized_overlay_image = LogoRenderer.get_resized_overlay(logo_path, 1280)
font = LogoRenderer.get_logo_font(font_path)

logo_start = time.time()
for i in range(0, 1000):
    logo_img = LogoRenderer.write(field, resized_overlay_image, font, "%d.%m.%Y", "%H%M", time.time())

print("Done in {} seconds.".format(time.time() - logo_start))

#cv2.imwrite("res.png", logo_img)


