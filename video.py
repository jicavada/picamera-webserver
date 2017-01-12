#!/usr/bin/env python

import cv2
import os
import os.path
import time
import pickle
from frame import Frame

class VideoProperties(object):
    def __init__(self):
        self.prop_version = 1
        self.undetected_frame_count = 0
        self.total_frame_count = 0
        self.video_path = ''
        self.real_fps = 0
        self.ideal_fps = 0
        self.xres = 0
        self.yres = 0
        self.pre_num_frames = 0
        self.post_num_frames = 0

    @staticmethod
    def path(path):
        return path + ".props"

    @staticmethod
    def exists(path):
        path = VideoProperties.path(path)
        return os.path.isfile(path)

    @staticmethod
    def load(path):
        path = VideoProperties.path(path)
        if not os.path.isfile(path):
            raise OSError("VideoProperties file not found {0}".format(path))

        with open(path, 'r') as f:
            return pickle.load(f)

    def save(self):
        path = VideoProperties.path(self.video_path)
        with open(path, 'wb') as f:
            pickle.dump(self, f)

class VideoPreviewGenerator(object):
    def __init__(self, path):
        self.video_path = path
        self.preview_path = VideoPreviewGenerator.path(path)
        if not os.path.exists(self.preview_path):
            os.makedirs(self.preview_path)

        self.props = VideoProperties.load(self.video_path)
        self.cap = cv2.VideoCapture(self.video_path)

    @staticmethod
    def path(path):
        return path + ".preview"

    @property
    def frame_count(self):
        return self.props.total_frame_count

    def equidistant_previews(self, num):
        if num <= 0:
            return []

        spacing = self.frame_count / num
        indexes = []
        for index in range(0, self.frame_count, spacing):
            indexes.append(index)

        return self.previews(indexes)

    def previews(self, indexes=[]):
        paths = []
        for index in range(0, self.frame_count):
            success, image = self.cap.read()
            if not success:
                break

            if index in indexes:
                preview_path = os.path.join(self.preview_path, "{0}.jpeg".format(index))
                if not os.path.exists(preview_path):
                    cv2.imwrite(preview_path, image, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
                paths.append(preview_path)

        return paths

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
        self.properties = {}
        self.__reset_properties()

    @property
    def base_path(self):
        folder = os.path.join(self.path, self.name)
        if not os.path.exists(folder):
            os.makedirs(folder)

        return folder

    def __build_path(self):
        folder = self.base_path
        recording = "{0}.{1}".format(time.strftime("%Y%m%d-%H%M%S"), self.video_extension)

        return os.path.join(folder, recording)

    def __reset_properties(self):
        self.props = VideoProperties()

    def __write_properties(self):
        self.props.save()

    def add_frame(self, current_frame, record):
        self.frame_stack.insert(0, current_frame.frame)

        self.props.real_fps = current_frame.real_fps
        self.props.ideal_fps = current_frame.ideal_fps
        self.props.xres = current_frame.xres
        self.props.yres = current_frame.yres
        self.props.pre_num_frames = int(self.predetect_time * self.props.real_fps)
        self.props.post_num_frames = int(self.postdetect_time * self.props.real_fps)
        generated_video = ''

        if not self.recording and record:
            self.props.video_path = self.__build_path()
            self.video_writer = cv2.VideoWriter(self.props.video_path, self.format, self.props.real_fps, (self.props.xres, self.props.yres))
            self.recording = True
            self.props.undetected_frame_count = 0
            print "Rec+: {0}".format(self.props.video_path)

        if self.recording == True:
            self.props.total_frame_count += 1

            if len(self.frame_stack) > 0:
                f = self.frame_stack.pop()
                self.video_writer.write(f)
                del f

                if not record:
                    self.props.undetected_frame_count += 1
                    video_required_frames = self.props.pre_num_frames + self.props.post_num_frames
                    if self.props.undetected_frame_count > video_required_frames:
                        print "Rec-"
                        del self.video_writer

                        self.recording = False
                        generated_video = self.props.video_path
                        self.__write_properties()
                        self.__reset_properties()
        else:
            for count in range(self.props.pre_num_frames, len(self.frame_stack)):
                print "Rec pop {0}: {1}".format(self.props.pre_num_frames, len(self.frame_stack))
                self.frame_stack.pop()

        return generated_video
