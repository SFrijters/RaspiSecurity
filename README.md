# RaspiSecurity
Home Surveillance with a Raspberry Pi with only ~100 lines of Python Code, forked from https://github.com/erogol/RaspiSecurity.
For technical details check the related [medium post](https://hackernoon.com/raspberrypi-home-surveillance-with-only-150-lines-of-python-code-2701bd0373c9). Hope you like it.

## Differences from the original
- Runs on a Raspberry Pi B; the script now works with OpenCV 2, which is what Wheezy has by default (no need to build OpenCV from source).
- Includes a script to run the server as a service.
- No longer supports Dropbox.
- Assumes the Raspberry Pi is also an SMTP server.

# Installation to a Raspberry Pi B

This readme has been updated after tweaking my installation, so it may be missing some steps.

## Install necessary libraries

- ```sudo apt-get update```
- ```sudo apt-get install python-picamera python-opencv postfix```
- Configure postfix to your liking

## Setup config files
- Set your email address to be noticed for each alert in [the config file](conf.json).
- NOTE: The script now assumes that ```127.0.0.1``` (localhost) is an SMTP server.

## Run the agent manually
- ```python server.py ```
- Go to given URL on the terminal
- Activate or deactivate the agent. The idea here is, if you are close to your house, your phone will connect to your net before you enter the house,
then you can deactivate the agent to prevent an alert. You should also activate it before leaving the house. It'll give you some time to leave the house then become active.

## Run the agent as a service
- Copy the ```etc/init.d/rpi-surveillance``` script to ```/etc/init.d```.
- ```sudo update-rc.d rpi-surveillance defaults```
- NOTE: This assumes the repo is cloned into ```/home/pi``` (edit the script if you want).

## Logwatch

If you are using Logwatch, you can copy/symlink the files in ```etc/logwatch``` into ```/etc``` to add rpi-surveillance as a service to watch.