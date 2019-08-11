#!/usr/bin/env python3
import os

from Shared.SharedFunctions import SharedFunctions


def run_main(file_type: str):
    source_dir = os.path.normpath(r"/var/tmp/sports-replay/video-making/00001-002-2019-08-03-12-20/2")
    files = [SharedFunctions.get_file_name_only(fi)
             for fi in os.listdir(source_dir)
             if os.path.isfile(os.path.join(source_dir, fi)) and fi.lower().endswith(".{}".format(file_type))]
    for fi in files:
        parts = fi.replace("frame_", "").split('_')
        source_file = os.path.normpath(r"{}/{}.{}".format(source_dir, fi, file_type))
        new_file = os.path.normpath(r"{}/frame_{}_{}.{}".format(source_dir,
                                                                int(parts[0]) + offset,
                                                                str(int(parts[1])).zfill(4), file_type))
        print("File renamed to {}".format(new_file))
        os.rename(source_file, new_file)


if __name__ == "__main__":
    offset = -7599
    run_main("jpg")
    run_main("json")
