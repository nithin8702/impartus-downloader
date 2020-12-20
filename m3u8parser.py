from typing import List
import re


class M3u8Parser:

    def __init__(self, content_list: List = None, num_tracks=1):
        if content_list:
            self.m3u8_content = content_list
        else:
            self.m3u8_content = []

        # [
        #   [ {file1, 02:00, key1, AES-128}, {file2, 01:00, key2, AES-128}, {file4, 00:30, None, None}    ],
        #   [ {file3, 02:00, key3, AES-128}, {file5, 01:00, None, None},    {file6, 00:30, key6, AES-128} ],
        # ]
        # above example is a 2-track file with track 1 consisting of stream files 1, 2, and 4
        # and track 2 consists of stream files 3, 5 and 6. Of these 1,2,3 and 6 are encrypted.
        self.tracks = [list() for x in range(num_tracks)]   # noqa
        self.summary = dict()

    def parse(self):

        current_track = 0
        current_file_number = -1
        current_file_duration = 0
        current_encryption_method = "NONE"
        current_encryption_key_file = None

        key_files = 0
        media_files = 0
        total_duration = 0
        for index, token in enumerate(self.m3u8_content):
            if str(token).startswith("#EXT-X-KEY:METHOD"):  # encryption algorithm
                current_encryption_method = re.sub(r"^#EXT-X-KEY:METHOD=([A-Z0-9-]+).*$", r"\1", token)
                if current_encryption_method == "NONE":
                    current_encryption_key_file = None
                else:
                    current_file_number += 1
                    key_files += 1
                    current_encryption_key_file = current_file_number
            elif str(token).startswith("#EXTINF:"):  # duration
                current_file_duration = float(re.sub(r'^#EXTINF:([0-9]+\.[0-9]+),.*', r"\1", token))
                total_duration += current_file_duration
            elif str(token).startswith("http"):  # media file
                current_file_number += 1
                media_files += 1
                self.tracks[current_track].append({
                    "file_number": current_file_number,
                    "duration": current_file_duration,
                    "encryption_key_file": current_encryption_key_file,
                    "encryption_method": current_encryption_method,
                })
            elif str(token).startswith("#EXT-X-DISCONTINUITY"):
                # do we need anything here ?
                pass
            elif str(token).startswith("#EXT-X-MEDIA-SEQUENCE"):    # switch view
                current_track = int(re.sub("#EXT-X-MEDIA-SEQUENCE:", '', token))
            elif str(token).startswith("#EXT-X-ENDLIST"):    # end of streams
                break
            else:
                continue

        self.summary = {
            "key_files": key_files,
            "media_files": media_files,
            "total_files": key_files + media_files,
            "total_duration": total_duration,   # combined of all tracks.
        }
        return self.summary, self.tracks