#!/usr/bin/env python

import cv2
import os
import time
from frame import Frame

class VideoBuffer(object):
    def __init__(self, name, path, predetect_time, postdetect_time):
        video_format = 'XVID'
        self.format = cv2.cv.CV_FOURCC(*video_format)
        self.force_record = False
        self.video_extension = "avi"
        self.name = name
        self.path = path
        self.predetect_time = predetect_time
        self.postdetect_time = postdetect_time
        self.frame_stack = []
        self.recording = False
        self.video_frame_count = 0

    def __build_path(self):
        folder = os.path.join(self.path, self.name)
        if not os.path.exists(folder):
            os.makedirs(folder)
        recording = "{0}.{1}".format(time.strftime("%Y%m%d-%H%M%S"), self.video_extension)

        return os.path.join(folder, recording)

    def add_frame(self, current_frame, record):
        self.frame_stack.insert(0, current_frame.frame)

        xres = current_frame.xres
        yres = current_frame.yres
        fps = current_frame.real_fps
        pre_num_frames = int(self.predetect_time * fps)
        post_num_frames = int(self.postdetect_time * fps)

        if not self.recording and record:
            video_path = self.__build_path()
            self.video_writer = cv2.VideoWriter(video_path, self.format, fps, (xres, yres))
            self.recording = True
            self.video_frame_count = 0
            print "Rec+: {0}".format(video_path)

        if self.recording == True:
            if len(self.frame_stack) > 0:
                f = self.frame_stack.pop()
                self.video_writer.write(f)
                del f

                if not record:
                    self.video_frame_count += 1
                    video_required_frames = pre_num_frames + post_num_frames
                    if self.video_frame_count > video_required_frames:
                        print "Rec-"
                        del self.video_writer
                        self.recording = False
        else:
            for count in range(pre_num_frames, len(self.frame_stack)):
                print "Rec pop {0}: {1}".format(pre_num_frames, len(self.frame_stack))
                self.frame_stack.pop()
