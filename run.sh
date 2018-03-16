#!/bin/bash

P4APPRUNNER=./utils/p4apprunner.py
rm -rf build
mkdir -p build
cp p4app.$1.json p4app.json
tar -czf build/p4app.tgz * --exclude='build'
#cd build
sudo python $P4APPRUNNER p4app.tgz --build-dir ./build
