"""
A model of a chapter of a manga.
"""

import logging
from bs4 import BeautifulSoup

from page import Page
from downloader import Downloader


logger = logging.getLogger(__name__)


class Chapter:
    """
    The chapter of a manga.

    Attributes:
        num (int): The numerical order of the chapter. Considered to be unique.
        url (str): The URL of the main manga page.
        title (str): The title of the manga.
        pages (list of Page): List of the pages of the manga.
    """

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self, num, url, title=None, pages=None):
        self.num = num
        self.url = url
        self.title = title
        self.pages = pages if pages is not None else []
        logger.debug('Initialized chapter %d: %s  (%s)  (%s)',
                     num, url, 'Untitled' if title is None else title,
                     'No pages' if pages is None else str(len(pages)))

    ##################################################
    # GETTERS
    ##################################################

    def getTitle(self, soup):
        """
        Get the chapter title from its soup.

        Parameters:
            soup (BeautifulSoup): The chapter HTML soup.

        Returns:
            str: The title of the chapter.
        """

        # TODO Implement manga-specific getTitle
        title = 'SampleChapterTitle'

        return title

    def getPages(self, soup):
        """
        Get the pages from the chapter's HTML soup.

        Parameters:
            soup (BeautifulSoup): The chapter HTML soup.

        Returns:
            list of Page: The list of Pages of the manga.
        """

        # TODO Implement manga-specific getChapters

        pageUrls = [
            'https://xkcd.com/201',
            'https://xkcd.com/202',
            'https://xkcd.com/203'
        ]

        # Instantiate a list of skeleton pages (pages containing only the url).
        pages = []
        for idx, pageUrl in enumerate(pageUrls):
            pages.append(Page(idx + 1, pageUrl))

        return pages

    ##################################################
    # UPDATE
    ##################################################

    def fetch(self):
        """
        Fetch the chapter HTML, parse it, and update the properties.
        Raises an error if the fetching or parsing failed.
        """
        soup = None
        logger.debug('Fetching chapter %d HTML from %s...', self.num, self.url)
        response, err = Downloader.get(self.url)
        if err is not None:
            raise err
        logger.debug('Successfully fetched chapter %d from %s...', self.num, self.url)

        logger.debug('Parsing chapter %d into soup...', self.num)
        soup = BeautifulSoup(response.text, 'html.parser')
        logger.debug('Successfully parsed chapter %d into soup.', self.num)

        self.updateWithSoup(soup)

    def updateWithSoup(self, soup):
        """
        Update the properties based on the chapter's HTML soup.
        Raises an error if the parsing failed.

        Parameters:
            soup (BeautifulSoup): The chapter's HTML soup.
        """
        # TODO - Change the implementation below to fit the specifics of your manga

        logger.debug('Updating chapter %d properties (%s) based on soup...', self.num, self.url)

        # Get the title of the chapter from its soup.
        title = self.getTitle(soup)

        # Get the page URLs. This may involve fetching other pages
        # if the main manga page doesn't contain all the chapter URLs.
        # The list should be in increasing order in terms of page number.
        pages = self.getPages(soup)

        # Update the properties
        self.title = title
        self.pages = pages

    ##################################################
    # REPRESENTATION
    ##################################################

    def __str__(self):
        result = f'   {self.num}: {self.url}  ({self.title})\n'
        if len(self.pages) > 0:
            result += '\n'.join(f'      {str(page)}' for page in self.pages)
        else:
            result += '      (no pages)'
        return result

    def __repr__(self):
        title = 'Untitled' if self.title is None else self.title
        pages = 'No pages' if len(self.pages) == 0 else f'{len(self.pages)} pages'
        return f'Chapter {self.num}: {self.url}  ({title})  ({pages})'
