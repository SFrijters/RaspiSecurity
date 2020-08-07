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

RPI_CAMERA_PID_FILE='/var/run/rpi-camera.pid'

def get_camera_pid():
    if not os.path.isfile(RPI_CAMERA_PID_FILE):
        return None
    with open(RPI_CAMERA_PID_FILE, 'r') as pid_file:
        return int(pid_file.read())

def set_camera_pid(pid):
    with open(RPI_CAMERA_PID_FILE, 'w+') as pid_file:
        pid_file.write("%d" % pid)


@app.before_first_request
def start_up():
    log.configureLogger(20)
    logger.info("Starting server")
    logger.info("Connect to http://%s:5555 to toggle the camera", get_ip_address())
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

def shutdown(*args):
    logger.info("Stopping camera")
    pid = get_camera_pid()
    if pid is not None:
        os.kill(pid, signal.SIGTERM)
        os.remove(RPI_CAMERA_PID_FILE)
        logger.debug("Camera process id = %d killed!", pid)
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
    logger.info("Starting camera")
    if get_camera_pid() is None:
        proc = subprocess.Popen(["python3", "camera.py", "-c", "conf.json"], preexec_fn=lambda: os.nice(10))
        set_camera_pid(proc.pid)
        logger.debug("Camera process id = %d", proc.pid)
    else:
        logger.info("Camera was already active")
    return "Start camera"

@app.route("/stop", methods=['GET', 'POST'])
def stop_camera():
    logger.info("Stopping camera")
    pid = get_camera_pid()
    if pid is not None:
        os.kill(pid, signal.SIGTERM)
        os.remove(RPI_CAMERA_PID_FILE)
        logger.debug("Camera process id = %d killed!", pid)
    else:
        logger.info("Camera was already inactive")
    return "Stop camera"

@app.route("/status", methods=['GET', 'POST'])
def status_camera():
    pid = get_camera_pid()
    if pid is None:
        logger.debug("Camera is inactive")
        return "Inactive"
    else:
        logger.debug("Camera running as pid = %d", pid)
        return "Running"

if __name__ == "__main__":
    log.configureLogger(20)
    try:
        app.run(host="0.0.0.0", port=5555, debug=False)
    except Exception as e:
        logger.exception(e)
