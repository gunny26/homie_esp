#!/bin/bash
#
#
# either ESP8266 or ESP32
# corresponding subdirectory with firmware
BOARD=ESP8266
# USB port to communicate
PORT=/dev/ttyUSB0
# port speed
BAUD=460800

if [ $BOARD == "ESP8266" ]; then
    # for ESP8266
    esptool.py --port $PORT erase_flash
    esptool.py --port $PORT --baud $BAUD write_flash --flash_size=detect --verify -fm dio 0x0 $BOARD/microhomie-esp8266-v3.0.2.bin
fi;

if [ $BOARD == "ESP32" ]; then
    # for ESP32
    esptool.py --chip esp32 --port $PORT erase_flash
    esptool.py --chip esp32 --port $PORT --baud $BAUD write_flash -z 0x1000 $BOARD/esp32-idf4-20200902-v1.13.bin
fi

echo "sleeping for 10s to wait for reset"
sleep 10

# screen communication speed
BAUD=115200
ampy -b $BAUD -p $PORT put  settings.py settings.py
ampy -b $BAUD -p $PORT put  main.py main.py
screen $PORT $BAUD
