#!/bin/bash

echo "Installing OpenCV"
apt-get install python-opencv || exit 1

echo "Installing Pip"
apt-get install python-pip || exit 1

echo "Installing dev headers for Python"
apt-get install python-dev || exit 1

echo "Installing dev headers for Python"
apt-get install libyaml-dev || exit 1

echo "Installing Flask"
pip install flask || exit 1

echo "Installing PyYAML"
pip install yaml || exit 1
