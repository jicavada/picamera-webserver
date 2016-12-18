#!/usr/bin/env python

import argparse
import time
import Pyro4
from frame import Frame
from camera import RemoteCamera
from web_api import WebAPI
from flask import Flask

can_run = True
cameras = []
app = Flask(__name__)

def on_run(args):
    Pyro4.config.COMMTIMEOUT = 1.0
    Pyro4.config.SERIALIZER = 'pickle'
    for addr in args.camera:
        cam = RemoteCamera(addr)
        cam.start()
        cameras.append(cam)

    web = WebAPI(app, cameras)

    print "Running"
    app.run(host='0.0.0.0', port=8081, debug=True, threaded=True)

    print "Cleaning up"
    for cam in cameras:
        cam.stop()


parser = argparse.ArgumentParser(description="Listens to streams from cameras and collates them into web viewable stream.\n")
parser.add_argument('-camera', help='Camera address in ip:port formation. Can be specified multiple times.', action='append', required=True)
parser.set_defaults(pir_active=False)
parser.set_defaults(func=on_run)
args = parser.parse_args()
args.func(args)
