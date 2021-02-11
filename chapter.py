"""
A model of a chapter of a manga.
"""

import logging
import weakref
from bs4 import BeautifulSoup

from page import Page
from downloader import Downloader


logger = logging.getLogger(__name__)


class Chapter:
    """
    The chapter of a manga.

    Attributes:
        manga (Manga): A weak reference to the parent manga.
        num (int): The numerical order of the chapter. Considered to be unique.
        url (str): The URL of the main manga page.
        title (str): The title of the manga.
        pages (list of Page): List of the pages of the manga.
    """

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self, manga, num, url, title=None, pages=None):
        self._manga = weakref.ref(manga)
        self.num = num
        self.url = url
        self.title = title
        self.pages = pages if pages is not None else []
        logger.debug("Initialized '%s' Chapter %d: %s  (%s)  (%s)",
                     manga.title, num, url, 'Untitled' if title is None else title,
                     'No pages' if pages is None else str(len(pages)))

    ##################################################
    # WEAK REF PROPERTIES
    ##################################################

    @property
    def manga(self):
        """
        A weak reference to the parent manga.
        Raises LookupError if parent is None.
        """
        if not self._manga:
            raise LookupError("Parent manga not found.")
        _manga = self._manga()
        if _manga:
            return _manga
        else:
            raise LookupError("Parent manga was destroyed.")

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
        title = f'SampleChapterTitle{self.num}'

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
        logger.debug("Parsing pages of '%s' Chapter %d from its soup...",
                     self.manga.title, self.num, )

        pageUrls = [
            'https://xkcd.com/201',
            'https://xkcd.com/202',
            'https://xkcd.com/203'
        ]

        # Instantiate a list of skeleton pages (pages containing only the url).
        pages = []
        for idx, pageUrl in enumerate(pageUrls):
            pages.append(Page(self, idx + 1, pageUrl))

        return pages

    def getDirectoryName(self):
        """
        Get the chapter directory name.

        Raises:
            AttributeError if the title is None.

        Returns:
            The manga directory name.
        """
        logger.debug("Converting '%s' Chapter %d title (%s) to directory name...",
                     self.manga.title, self.num, self.title)

        if self.title is None:
            raise AttributeError('Chapter title not found.')

        dirName = self.title
        invalidFilenameChars = '<>:"/\\|?*.'
        for invalidChar in invalidFilenameChars:
            dirName = dirName.replace(invalidChar, '_')

        logger.debug("Directory name of '%s' Chapter %d is '%s'.",
                     self.manga.title, self.num, dirName)
        return dirName

    ##################################################
    # UPDATE
    ##################################################

    def fetch(self):
        """
        Fetch the chapter HTML, parse it, and update the properties.
        Raises an error if the fetching or parsing failed.
        """
        logger.debug("Fetching '%s' Chapter %d HTML from %s...",
                     self.manga.title, self.num, self.url)

        soup = None

        # Send HTTP request to get chapter HTML
        response, err = Downloader.get(self.url)
        # If the HTTP request failed, raise the error
        if err is not None:
            raise err

        logger.debug("Successfully fetched '%s' Chapter %d from %s...",
                     self.manga.title, self.num, self.url)

        logger.debug("Parsing '%s' Chapter %d into soup...", self.manga.title, self.num)
        soup = BeautifulSoup(response.text, 'html.parser')
        logger.debug("Successfully parsed '%s' Chapter %d into soup.", self.manga.title, self.num)

        self.updateWithSoup(soup)

    def updateWithSoup(self, soup):
        """
        Update the properties based on the chapter's HTML soup.
        Raises an error if the parsing failed.

        Parameters:
            soup (BeautifulSoup): The chapter's HTML soup.
        """
        # TODO - Change the implementation below to fit the specifics of your manga

        logger.debug("Updating '%s' Chapter %d based on soup...", self.manga.title, self.num)

        # Get the title of the chapter from its soup.
        title = self.getTitle(soup)

        # Get the page URLs. This may involve fetching other pages
        # if the main manga page doesn't contain all the chapter URLs.
        # The list should be in increasing order in terms of page number.
        pages = self.getPages(soup)

        # Update the properties
        self.title = title
        self.pages = pages

        logger.debug("Chapter %d of '%s' has been updated.", self.num, self.manga.title)

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
