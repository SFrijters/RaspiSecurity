# -*- coding: utf-8 -*-

from picamera.array import PiRGBArray
from picamera import PiCamera
import argparse
import datetime
import json
import time
import cv2
import os
import tempfile

import log
import logging
logger = logging.getLogger("rpi-surveillance-camera")
logger.addHandler(logging.NullHandler())

def send_email(config):

    from email.mime.application import MIMEApplication
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.utils import formatdate
    import smtplib
    import glob

    logger.debug("Emailing to %s", config['email_to'])
    text = ""
    subject = "RPi Surveillance Security Alert %s" % datetime.datetime.now().strftime(log.TIME_FORMAT_SHORT)

    msg = MIMEMultipart()
    msg['From'] = config['email_from']
    msg['To']   = config['email_to']
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(text))

    # set attachments
    files = glob.glob("/tmp/surveillance*")
    logger.debug("Number of images attached to email: %d", len(files))
    for f in files:
        with open(f, "rb") as fil:
            part = MIMEApplication(fil.read(), Name=os.path.basename(f))
            part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(f)
            msg.attach(part)

    # The actual mail send
    server = smtplib.SMTP('127.0.0.1')
    server.sendmail(config['email_from'], config['email_to'], msg.as_string())
    server.quit()

def main():
    # construct the argument parser and parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--conf", help="path to the JSON configuration file", default="conf.json")
    parser.add_argument("-v", default=20, help="Verbosity")
    options = parser.parse_args()

    log.configureLogger(options.v)

    logger.debug("Loading camera config file")
    with open(options.conf, 'r') as config_file:
        config = json.load(config_file)

    # initialize the camera and grab a reference to the raw camera capture
    logger.debug("Initializing camera")
    camera = PiCamera()
    camera.resolution = tuple(config["resolution"])
    camera.framerate = int(config["fps"])
    logger.debug("Initializing rawCapture")
    rawCapture = PiRGBArray(camera, size=camera.resolution)

    # allow the camera to warmup, then initialize the average frame, last
    # uploaded timestamp, and frame motion counter
    warmup = config["camera_warmup_time"]
    logger.debug("Warming up the camera for %d seconds", warmup)
    time.sleep(warmup)
    avg = None
    lastUploaded = datetime.datetime.now()
    motionCounter = 0
    logger.debug("Surveillance started")

    # capture frames from the camera
    for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        # grab the raw NumPy array representing the image and initialize
        # the timestamp and occupied/unoccupied text
        frame = f.array

        ######################################################################
        # COMPUTER VISION
        ######################################################################
        # resize the frame, convert it to grayscale, and blur it
        # TODO: resize image here into cmaller sizes
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, tuple(config['blur_size']), 0)

        # if the average frame is None, initialize it
        if avg is None:
            logger.debug("Initializing background model")
            avg = gray.copy().astype("float")
            rawCapture.truncate(0)
            continue

        # accumulate the weighted average between the current frame and previous frames,
        # then compute the difference between the current frame and running average
        frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
        cv2.accumulateWeighted(gray, avg, 0.5)

        # threshold the delta image, dilate the thresholded image to fill
        # in holes, then find contours on thresholded image
        thresh = cv2.threshold(frameDelta, config["delta_thresh"], 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        _, cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # loop over the contours
        frameIsOccupied = False
        for c in cnts:
            if cv2.contourArea(c) < config["min_area"]: continue

            # compute the bounding box for the contour, draw it on the frame, and update the text
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            frameIsOccupied = True

        ###################################################################################
        # LOGIC
        ###################################################################################

        # check to see if the room is occupied
        if frameIsOccupied:

            # draw the text and timestamp on the frame
            timestamp = datetime.datetime.now()
            ts = timestamp.strftime(log.TIME_FORMAT_LONG)
            # text = "Occupied" if frameIsOccupied else "Unoccupied"
            # cv2.putText(frame, "Room Status: {}".format(text), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

            # save occupied frame
            cv2.imwrite(os.path.join(tempfile.gettempdir(),"surveillance_{}.jpg".format(motionCounter)), frame)

            # check to see if enough time has passed between uploads
            if (timestamp - lastUploaded).seconds >= config["min_upload_seconds"]:

                # increment the motion counter
                motionCounter += 1

                # check to see if the number of frames with consistent motion is high enough
                if motionCounter >= config["min_motion_frames"]:
                    logger.info("Sending an alert email")
                    send_email(config)

                    logger.debug("Warming up the camera for %d seconds", warmup)
                    time.sleep(warmup)
                    avg = None
                    lastUploaded = datetime.datetime.now()
                    motionCounter = 0
                    logger.debug("Surveillance started")

        # otherwise, the room is not occupied
        else:
            motionCounter = 0

        # clear the stream in preparation for the next frame
        rawCapture.truncate(0)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(e)

