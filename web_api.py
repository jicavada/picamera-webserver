#!/usr/bin/env python

import threading
import time
import cv2
from frame import Frame
from flask import Flask, request, render_template, Response, jsonify, send_from_directory

class WebAPI(object):
    def __init__(self, app, cameras, title):
        self.app = app
        self.cameras = cameras
        self.title = title
        self.app.add_url_rule('/', endpoint='index', view_func=self.index)
        self.app.add_url_rule('/cameras/<int:index>', endpoint='camera_feed', view_func=self.camera_feed)
        self.app.add_url_rule('/cameras_raw/<int:index>', endpoint='camera_feed_raw', view_func=self.camera_feed_raw)
        self.app.add_url_rule('/cameras_all', endpoint='camera_feed_all', view_func=self.camera_feed_all)
        self.app.add_url_rule('/recordings', endpoint='recordings', view_func=self.recordings)
        self.app.add_url_rule('/detected_raw/<int:index>', endpoint='detected_raw', view_func=self.detected_raw)
        self.app.add_url_rule('/rec_list/<int:index>', endpoint='rec_list', view_func=self.rec_list)
        self.app.add_url_rule('/rec_preview_raw/<int:index>/<string:name>', endpoint='rec_preview_raw', view_func=self.rec_preview_raw)
        self.app.add_url_rule('/rec_download/<int:index>/<string:name>', endpoint='rec_download', view_func=self.rec_download)
        self.app.add_url_rule('/<path:path>', endpoint='unknown', view_func=self.unknown)

    def index(self):
        return render_template('index.html', cameras=self.cameras, title=self.title)

    def unknown(self, path):
        return render_template('404.html'), 404

    def camera_feed(self, index):
        if index == 0 or index > len(self.cameras):
            return render_template('404.html'), 404

        return render_template('camera_feed.html', index=index, cam=self.cameras[index - 1])

    def recordings(self):
        return render_template('recordings.html', cameras=self.cameras)

    def rec_list(self, index):
        if index == 0 or index > len(self.cameras):
            return render_template('404.html'), 404

        return render_template('rec_list.html', index=index, cam=self.cameras[index - 1])

    def __gen_preview(self, camera, name):
        rec = camera.recordings[name]

        while True:
            for path in rec.preview_paths:
                print("Loading: {0}".format(path))
                frame = cv2.imread(path)
                frame = cv2.imencode(".jpeg", frame, (cv2.IMWRITE_JPEG_QUALITY,80))[1]
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame.tostring() + b'\r\n')
                time.sleep(4)

    def rec_preview_raw(self, index, name):
        if index == 0 or index > len(self.cameras):
            return render_template('404.html'), 404

        camera = self.cameras[index - 1]
        if name not in camera.recordings:
            return render_template('404.html'), 404

        return Response(self.__gen_preview(camera, name),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    def rec_download(self, index, name):
        if index == 0 or index > len(self.cameras):
            return render_template('404.html'), 404

        camera = self.cameras[index - 1]
        if name not in camera.recordings:
            return render_template('404.html'), 404

        rec = camera.recordings[name]

        return send_from_directory(directory=rec.directory, filename=rec.filename)

    def camera_feed_raw(self, index):
        if index == 0 or index > len(self.cameras):
            return render_template('404.html'), 404

        return Response(self.__gen_camera_feed(self.cameras[index - 1]),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    def camera_feed_all(self):
        return render_template('camera_feed_all.html', cameras=self.cameras)

    def detected_raw(self, index):
        if index == 0 or index > len(self.cameras):
            return render_template('404.html'), 404

        return jsonify(pir_detected=self.cameras[index - 1].detected())

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
