#!/usr/bin/env python

import threading
import time
import Pyro4
from frame import Frame

class RemoteCamera(object):
    def __init__(self, address):
        self.uri_string = "PYRO:core_server@{0}".format(address)
        self.current_frame = None
        self.pir_detected = False

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

    def on_read_frames(self):
        print "{0} starting".format(self.uri_string)
        last_timestamp = time.time()
        camera = Pyro4.Proxy(self.uri_string)

        while self.can_run:
            try:
                self.current_frame = camera.get_frame()
            except Pyro4.errors.ConnectionClosedError:
                print "{0} reconnecting".format(self.uri_string)
                camera._pyroReconnect()
            self.pir_detected = camera.get_pir_state()

            now_timestamp = time.time()
            diff = now_timestamp - last_timestamp
            last_timestamp = now_timestamp
            fps = 1 / diff
            print "{0} network fps: {1:.2f} | camera fps: {2:.2f}".format(self.uri_string, fps, self.current_frame.fps)

        print "{0} stopping".format(self.uri_string)
        self.stopped.set()

