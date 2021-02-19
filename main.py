"""
The main entry to the manga crawler script.
"""


import os
import logging

from log import initializeLogger
from crawl import MangaCrawler
import impl


logger = logging.getLogger(__name__)

CHAPTER_THREAD_COUNT = 1
PAGE_THREAD_COUNT = 5


def main():
    """
    Main function.
    """
    # Initialize the logger
    initializeLogger()

    # Create the output directory
    os.makedirs(impl.OUTPUT_DIR, exist_ok=True)

    crawler = MangaCrawler(impl.MANGA_LIST, CHAPTER_THREAD_COUNT,
                           PAGE_THREAD_COUNT, impl.OUTPUT_DIR)
    crawler.crawl()


if __name__ == '__main__':
    try:
        main()
    except Exception as err:  # pylint: disable=broad-except
        logger.error('An unexpected exception escaped to the surface, %s', err)
        logger.exception(err)
