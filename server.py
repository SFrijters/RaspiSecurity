# -*- coding: utf-8 -*-

import os
import socket
import subprocess
import signal
from flask import Flask, render_template
app = Flask(__name__)

import log
import logging
logger = logging.getLogger("rpi-surveillance-server")
logger.addHandler(logging.NullHandler())

# Stop HTTP request spam
logging.getLogger('werkzeug').setLevel(logging.ERROR)

proc = None

def shutdown(*args):
    global proc
    logger.info("Stopping camera")
    if proc:
        try:
            proc.kill()
            logger.debug("Camera process id = %d killed!", proc.pid)
            proc = None
        except OSError:
            logger.warning("Failed to kill camera process")
    logger.info("Stopping server")
    os._exit(0)

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

@app.route("/")
def hello():
    return render_template("index.html")

@app.route("/start", methods=['GET', 'POST'])
def start_camera():
    global proc
    logger.info("Starting camera")
    if proc is None:
        proc = subprocess.Popen(["python", "camera.py", "-c", "conf.json"])
        logger.debug("Camera process id = %d", proc.pid)
    else:
        logger.info("Camera was already active")
    return "Start camera"

@app.route("/stop", methods=['GET', 'POST'])
def stop_camera():
    global proc
    logger.info("Stopping camera")
    if proc:
        try:
            proc.kill()
            logger.debug("Camera process id = %d killed!", proc.pid)
            proc = None
        except OSError:
            logger.warning("Failed to kill camera process")
    else:
        logger.info("Camera was already inactive")
    return "Stop camera"

@app.route("/status", methods=['GET', 'POST'])
def status_camera():
    global proc
    if proc is None:
        logger.debug("Camera is inactive")
        return "Inactive"
    if proc.poll() is None:
        logger.debug("Camera running as pid = %d", proc.pid)
        return "Running"
    else:
        logger.debug("Camera is inactive")
        return "Inactive"

if __name__ == "__main__":
    log.configureLogger(20)
    try:
        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)
        logger.info("Starting server")
        logger.info("Connect to http://%s:5555 to toggle the camera", get_ip_address())
        app.run(host="0.0.0.0", port=5555, debug=False)
    except Exception as e:
        logger.error(e)
