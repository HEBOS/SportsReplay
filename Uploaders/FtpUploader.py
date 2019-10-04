from ftplib import FTP
import os
import time


class FtpUploader(object):
    def __init__(self, host: str, username: str, password: str):
        self._host = host
        self._username = username
        self._password = password
        self._bytes_sent = 0
        self._total_bytes = 0

    def upload(self, source_path: str, target_file_name: str, create_terminator_file: bool):
        self._bytes_sent = 0
        with FTP() as ftp:
            ftp.debugging = 1
            ftp.connect(self._host, 21)
            ftp.login(user=self._username, passwd=self._password)
            self._total_bytes = os.path.getsize(source_path)
            with open(source_path, 'rb') as fp:
                ftp.storbinary(cmd='STOR ' + target_file_name, fp=fp, callback=self.report_progress, blocksize=102400)

            if create_terminator_file:
                with open(source_path + ".ready", 'w+') as fp:
                    fp.write("Video file uploaded at {}".format(time.strftime("%d-%m-%Y-%H-%M",
                                                                              time.localtime(time.time()))))

                    ftp.storlines(cmd='STOR ' + target_file_name + ".ready", fp=fp)
            ftp.close()

    def report_progress(self, buff):
        self._bytes_sent += len(buff)
        progress = int((self._bytes_sent / self._total_bytes) * 100)
        if progress % 10 == 0:
            print("Uploading files to {} - {}%".format(self._host, progress))
