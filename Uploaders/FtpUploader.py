from ftplib import FTP
import os
import time


class FtpUploader(object):
    def __init__(self, host: str, username: str, password: str, target_folder: str):
        self._host = host
        self._username = username
        self._password = password
        self._target_folder = target_folder
        self._bytes_sent = 0
        self._total_bytes = 0

    def upload(self, source_path: str, target_file_name: str, create_terminator_file: bool):
        self._bytes_sent = 0
        with FTP(host=self._host, user=self._username, passwd=self._password) as ftp:
            ftp.login(user=self._username, passwd=self._password)
            ftp.cwd(os.path.normpath(self._target_folder))
            self._total_bytes = os.path.getsize(source_path)
            with open(source_path, 'rb') as fp:
                ftp.storbinary(cmd='STOR ' + target_file_name, fp=fp, callback=self.report_progress)

            if create_terminator_file:
                with open(source_path + ".ready", 'w+') as fp:
                    fp.write("Video file uploaded at {}".format(time.strftime("%d-%m-%Y-%H-%M",
                                                                              time.localtime(time.time()))))

                    ftp.storlines(cmd='STOR ' + target_file_name, fp=fp)
            ftp.close()

    def report_progress(self, buff):
        self._bytes_sent += len(buff)
        print("Uploading files to {} - {}%".format(self._host, int(self._bytes_sent / self._total_bytes)))


if __name__ == "__main__":
    uploader = FtpUploader("sports-replay-ai-1", "pi", "Spswd001.", "streaming")
    uploader.upload(os.path.normpath("/home/sportsreplay/tmp/streaming/00001-002-2019-09-01-21-42.mp4v"),
                    "00001-002-2019-09-01-21-42.mp4v",
                    True)
