#!/usr/bin/env python

import argparse
import time
import Pyro4
from frame import Frame
from camera import RemoteCamera
from web_api import WebAPI
from flask import Flask
import yaml

can_run = True
cameras = []
app = Flask(__name__)

def on_run(args):
    Pyro4.config.COMMTIMEOUT = 1.0
    Pyro4.config.SERIALIZER = 'pickle'

    with open(args.config, 'r') as stream:
        try:
            config = yaml.load(stream)
        except yaml.YAMLError as exc:
            print exc

    for camera in config['cameras']:
        addr = camera['address']
        name = camera['name']
        port = camera['port']
        cam = RemoteCamera(name, addr, port)
        cam.start()
        cameras.append(cam)

    print "Running"
    webserver_config = config['webserver']
    web = WebAPI(app, cameras, webserver_config['title'])
    app.run(host=webserver_config['address'], port=webserver_config['port'], debug=True, threaded=True)

    print "Cleaning up"
    for cam in cameras:
        cam.stop()


parser = argparse.ArgumentParser(description="Listens to streams from cameras and collates them into web viewable stream.\n")
parser.add_argument('-config', help='Path to config file.', required=True)
parser.set_defaults(pir_active=False)
parser.set_defaults(func=on_run)
args = parser.parse_args()
args.func(args)
