"""
The main entry to the manga crawler script.
"""

import os

from log import initializeLogger
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
    initializeLogger()

    # Create the output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    crawler = MangaCrawler(MANGA_LIST, CHAPTER_THREAD_COUNT, PAGE_THREAD_COUNT, OUTPUT_DIR)
    crawler.crawl()


if __name__ == '__main__':
    main()
