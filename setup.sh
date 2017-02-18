#!/bin/bash

echo "Installing OpenCV"
apt-get install python-opencv || exit 1

echo "Installing Pip"
apt-get install python-pip || exit 1

echo "Installing Pyro4"
apt-get install python2-pyro4 || exit 1

echo "Installing Flask"
apt-get install python-flask || exit 1

echo "Installing YAML"
apt-get install python-yaml || exit 1

echo "Installing LZ4"
pip install lz4 --upgrade || exit 1
