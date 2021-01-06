#!/bin/bash
PORT=/dev/ttyUSB0
ampy -b 115200 -p $PORT put settings.py
ampy -b 115200 -p $PORT put main.py
screen $PORT 115200
