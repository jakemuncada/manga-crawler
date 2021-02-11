"""
Functions related to initializing and setting up the logging.
"""

import os
import logging
from logging.handlers import RotatingFileHandler

# The maximum size of a log file
MAX_BYTES = 10000000

# The number of log files to keep
BACKUP_COUNT = 10


def initializeLogger():
    """
    Initialize the logger.
    """
    # Set the global logging level to DEBUG
    logging.getLogger().setLevel(logging.DEBUG)

    # Disable 'noisy' libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('chardet').setLevel(logging.WARNING)

    initializeConsoleHandler()
    initializeFileHandler()


def initializeConsoleHandler():
    """
    Initialize the handler that will display logs to the console.
    """
    consoleHandler = logging.StreamHandler()

    # Set formatter to print only the message in console
    formatter = logging.Formatter('%(message)s')
    consoleHandler.setFormatter(formatter)

    # Set level to INFO
    consoleHandler.setLevel(logging.INFO)

    # Do not show exception traces in console
    logFilter = logging.Filter()
    logFilter.filter = lambda record: not record.exc_info
    consoleHandler.addFilter(logFilter)

    # Add the console handler to the root logger
    logging.getLogger().addHandler(consoleHandler)


def initializeFileHandler():
    """
    Initialize the handler that will log messages to a rotating log file.
    """
    # Create the log directory
    os.makedirs('./logs', exist_ok=True)

    # Set the log format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fileHandler = RotatingFileHandler('./logs/app.log', encoding='utf-8',
                                      maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT)
    fileHandler.setFormatter(formatter)

    # Set the log level to DEBUG so that everything will be written to the log file
    fileHandler.setLevel(logging.DEBUG)

    # Add the file handlser to the root logger
    logging.getLogger().addHandler(fileHandler)
