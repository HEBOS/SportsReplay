frame_number = 1000
fps = 25

total_seconds = int(frame_number / fps)
hours = int(total_seconds / 3600)
minutes = int(int(total_seconds - (hours * 3600)) / 60)
seconds = total_seconds - (hours * 3600) - (minutes * 60)

print("{}:{}:{}".format(str(int(hours)).zfill(2),
                         str(minutes).zfill(2),
                         str(seconds).zfill(2)))