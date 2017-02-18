#!/usr/bin/env python

import threading
import time
import Pyro4
import os
import os.path
import lz4
import numpy
import cv
import cv2
from frame import Frame
from video import VideoBuffer, VideoPreviewGenerator, VideoProperties

class Recording(object):
    def __init__(self, path):
        self.path = path
        self.directory = os.path.dirname(path)
        self.filename = os.path.basename(path)
        self.name, self.ext = os.path.splitext(self.filename)
        self.preview_paths = []

    def generate_previews(self, num):
        try:
            gen = VideoPreviewGenerator(self.path)
        except OSError as e:
            print(e)
            return
        self.preview_paths = gen.equidistant_previews(num)

class RemoteCamera(object):
    def __init__(self, name, address, port, rec_path, predetect_time, postdetect_time, preview_frame_count):
        self.name = name
        self.uri_string = "PYRO:core_server@{0}:{1}".format(address, port)
        self.current_frame = None
        self.pir_detected = False
        self.force_record = False
        self.preview_frame_count = preview_frame_count
        self.video_buffer = VideoBuffer(name, rec_path, predetect_time, postdetect_time)
        self.recordings = {}
        for f in os.listdir(self.video_buffer.base_path):
            p = os.path.join(self.video_buffer.base_path, f)
            if VideoProperties.exists(p):
                print 'Recording loaded: {0}'.format(p)
                rec = Recording(p)
                rec.generate_previews(4)
                self.recordings[rec.name] = rec
            elif p.endswith(self.video_buffer.video_extension):
                print 'Recording ignored due to missing properties: {0}'.format(p)

    def start(self):
        self.can_run = True
        self.stopped = threading.Event()
        t = threading.Thread(target=self.on_read_frames)
        t.daemon = True
        t.start()

    def stop(self, timeout=1):
        self.can_run = False
        self.stopped.wait(timeout)

    def frame(self):
        return self.current_frame

    def detected(self):
        return self.pir_detected

    def record(self):
        self.force_record = True

    def stop(self):
        self.force_record = False

    def on_read_frames(self):
        print "{0} starting".format(self.uri_string)
        last_timestamp = time.time()
        camera = Pyro4.Proxy(self.uri_string)
        recording = False

        while self.can_run:
            try:
                frame = camera.get_frame()
            except Pyro4.errors.ConnectionClosedError:
                print "{0} reconnecting".format(self.uri_string)
                camera._pyroReconnect()
                continue
            except Pyro4.errors.CommunicationError:
                print "{0} connecting".format(self.uri_string)
                camera._pyroReconnect()
                continue

            if frame.format == "str_lz4":
                frame_data = lz4.decompress(frame.frame)
                array = numpy.fromstring(frame_data, dtype='uint8')
                mat = cv.CreateMat(frame.yres, frame.xres, cv.CV_8UC3)
                cv.SetData(mat, frame_data)
                frame.frame = numpy.asarray(mat)
            elif frame.format == "str_jpeg":
                array = numpy.fromstring(frame.frame, dtype='uint8')
                frame_data = cv2.imdecode(array, cv2.IMREAD_UNCHANGED)
                mat = cv.CreateMat(frame.yres, frame.xres, cv.CV_8UC3)
                cv.SetData(mat, frame_data)
                frame.frame = numpy.asarray(mat)
            elif frame.format == "str_none":
                array = numpy.fromstring(frame.frame, dtype='uint8')
                mat = cv.CreateMat(frame.yres, frame.xres, cv.CV_8UC3)
                cv.SetData(mat, array)
                frame.frame = numpy.asarray(mat)
            else:
                print "Unknown frame format: {0}".format(frame.format)
                continue

            self.current_frame = frame

            # Need to override frame in frame for video buffer to work
            self.pir_detected = camera.get_pir_state()
            ideal_fps = self.current_frame.ideal_fps
            real_fps = self.current_frame.real_fps

            record = self.pir_detected or self.force_record or True
            generated_video = self.video_buffer.add_frame(self.current_frame, record)
            if generated_video:
                rec = Recording(generated_video)
                self.recordings[rec.name] = rec
                rec.generate_previews(self.self.preview_frame_count)

            now_timestamp = time.time()
            diff = now_timestamp - last_timestamp
            last_timestamp = now_timestamp
            fps = 1 / diff
            print "{0} network fps: {1:.2f} | camera fps: {2:.2f} | ideal fps: {3:.2f}".format(self.uri_string, fps, real_fps, ideal_fps)


        print "{0} stopping".format(self.uri_string)
        self.stopped.set()

