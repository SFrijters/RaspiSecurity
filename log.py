# -*- coding: utf-8 -*-

import logging
import logging.handlers
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

logLevel = logging.DEBUG

LOG_FORMAT_SHORT  = '%(message)s'
LOG_FORMAT_TIME   = '%(asctime)s - %(message)s'
LOG_FORMAT_LONG   = '%(asctime)s - pid %(process)d - %(name)s - %(levelname)s - %(message)s'
LOG_FORMAT_SYS    = '%(name)s - %(levelname)s - %(message)s'
TIME_FORMAT_LONG  = '%Y-%m-%d %H:%M:%S'
TIME_FORMAT_SHORT = '%H:%M:%S'

def configureLogger(level=logging.DEBUG):
    """
    Configure logger by adding a StreamHandler and an (optional) FileHandler.
    The StreamHandler will log at level 'level' (which can be either an integer
    or a string), while the FileHandler will log at logging.DEBUG level and
    be more verbose.
    """
    global logLevel
    logger = logging.getLogger()
    try:
        streamLevel = int(level)
    except ValueError:
        streamLevel = logging.getLevelName(str(level).upper())
    logger.setLevel(logging.DEBUG)
    logLevel = streamLevel
    # Set up console logging
    ch = logging.StreamHandler()
    ch.setLevel(streamLevel)
    cformatter = logging.Formatter(LOG_FORMAT_LONG, TIME_FORMAT_SHORT)
    ch.setFormatter(cformatter)
    logger.addHandler(ch)

    shandler = logging.handlers.SysLogHandler(address='/dev/log')
    shandler.setLevel(logging.INFO)
    fformatter = logging.Formatter(LOG_FORMAT_SYS, TIME_FORMAT_LONG)
    shandler.setFormatter(fformatter)
    logger.addHandler(shandler)
