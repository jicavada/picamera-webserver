#!/usr/bin/env python

import threading
import time
import Pyro4
from frame import Frame
from video import VideoBuffer

class RemoteCamera(object):
    def __init__(self, name, address, port, rec_path, predetect_time, postdetect_time):
        self.name = name
        self.uri_string = "PYRO:core_server@{0}:{1}".format(address, port)
        self.current_frame = None
        self.pir_detected = False
        self.force_record = False
        self.video_buffer = VideoBuffer(name, rec_path, predetect_time, postdetect_time)

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
                self.current_frame = camera.get_frame()
            except Pyro4.errors.ConnectionClosedError:
                print "{0} reconnecting".format(self.uri_string)
                camera._pyroReconnect()
                continue
            except Pyro4.errors.CommunicationError:
                print "{0} connecting".format(self.uri_string)
                camera._pyroReconnect()
                continue

            self.pir_detected = camera.get_pir_state()
            ideal_fps = self.current_frame.ideal_fps
            real_fps = self.current_frame.real_fps

            record = self.pir_detected or self.force_record
            self.video_buffer.add_frame(self.current_frame, record)

            now_timestamp = time.time()
            diff = now_timestamp - last_timestamp
            last_timestamp = now_timestamp
            fps = 1 / diff
            print "{0} network fps: {1:.2f} | camera fps: {2:.2f} | ideal fps: {3:.2f}".format(self.uri_string, fps, real_fps, ideal_fps)


        print "{0} stopping".format(self.uri_string)
        self.stopped.set()

