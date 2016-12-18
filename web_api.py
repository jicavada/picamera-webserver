#!/usr/bin/env python

import threading
import time
import cv2
from frame import Frame
from flask import Flask, request, render_template, Response

class WebAPI(object):
    def __init__(self, app, cameras):
        self.app = app
        self.cameras = cameras
        self.app.add_url_rule('/', endpoint='index', view_func=self.index)
        self.app.add_url_rule('/cameras/<int:index>', endpoint='camera_feed', view_func=self.camera_feed)
        self.app.add_url_rule('/cameras_raw/<int:index>', endpoint='camera_feed_raw', view_func=self.camera_feed_raw)
        self.app.add_url_rule('/<path:path>', endpoint='unknown', view_func=self.unknown)

    def index(self):
        return render_template('index.html', cameras=self.cameras)

    def unknown(self, path):
        return render_template('404.html'), 404

    def camera_feed(self, index):
        if index == 0 or index > len(self.cameras):
            return render_template('404.html'), 404

        return render_template('camera_feed.html', index=index)

    def __gen_camera_feed(self, camera):
        while True:
            img = camera.frame().frame
            bordersize = 5
            if camera.detected():
                color = [0, 255, 0]
            else:
                color = [0, 0, 0]
            frame = cv2.copyMakeBorder(img, bordersize, bordersize, bordersize, bordersize, cv2.BORDER_CONSTANT, value=color)
            frame = cv2.imencode(".jpeg", frame, (cv2.IMWRITE_JPEG_QUALITY,80))[1]
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame.tostring() + b'\r\n')

    def camera_feed_raw(self, index):
        if index == 0 or index > len(self.cameras):
            return render_template('404.html'), 404

        return Response(self.__gen_camera_feed(self.cameras[index - 1]),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
