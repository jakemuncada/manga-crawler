"""
The main entry to the manga crawler script.
"""

import os
import logging
from crawl import MangaCrawler


OUTPUT_DIR = './output'

CHAPTER_THREAD_COUNT = 1
PAGE_THREAD_COUNT = 3

MANGA_LIST = [
]


def main():
    """
    Main function.
    """
    # Initialize the logger
    initLogging()

    # Create the output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    crawler = MangaCrawler(MANGA_LIST, CHAPTER_THREAD_COUNT, PAGE_THREAD_COUNT, OUTPUT_DIR)
    crawler.crawl()


def initLogging():
    """
    Initialize the logger.
    """

    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('chardet').setLevel(logging.WARNING)

    handler = logging.StreamHandler()

    # Set formatter to print only the message in console
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)

    # Set level to INFO
    handler.setLevel(logging.INFO)

    logging.getLogger().addHandler(handler)


if __name__ == '__main__':
    main()
