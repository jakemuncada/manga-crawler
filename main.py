import os
import logging
from crawl import MangaCrawler


OUTPUT_DIR = './output'


def main():
    """
    Main function.
    """
    # Initialize the logger
    initLogging()

    # Create the output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    crawler = MangaCrawler(['https://stackoverflow.com'], 1, 3, OUTPUT_DIR)
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
    handler.setLevel(logging.DEBUG)

    logging.getLogger().addHandler(handler)


if __name__ == '__main__':
    main()
