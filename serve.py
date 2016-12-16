#!/usr/bin/env python

import argparse
import time
import signal
import Pyro4
from camera import RemoteCamera

can_run = True

def signal_handler(signal, frame):
    global can_run
    print "Ctrl+C caught, Quitting"
    can_run = False

def on_run(args):
    global can_run

    signal.signal(signal.SIGINT, signal_handler)
    Pyro4.config.COMMTIMEOUT = 1.0
    Pyro4.config.SERIALIZER = 'pickle'
    cameras = []
    for addr in args.camera:
        cam = RemoteCamera(addr)
        cam.start()
        cameras.append(cam)

    print "Running"
    while can_run:
        time.sleep(0.01)

    print "Cleaning up"
    for cam in cameras:
        cam.stop()

parser = argparse.ArgumentParser(description="Listens to streams from cameras and collates them into web viewable stream.\n")
parser.add_argument('-camera', help='Camera address in ip:port formation. Can be specified multiple times.', action='append', required=True)
parser.set_defaults(pir_active=False)
parser.set_defaults(func=on_run)
args = parser.parse_args()
args.func(args)
