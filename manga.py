"""
A model of the manga to be downloaded.
"""

import logging
from bs4 import BeautifulSoup

from chapter import Chapter
from downloader import Downloader


logger = logging.getLogger(__name__)


class Manga:
    """
    The manga to be downloaded.

    Attributes:
        url (str): The URL of the main manga page.
        title (str): The title of the manga.
        chapters (list of Chapter): List of the chapters of the manga.
    """

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self, url, title=None, chapters=None):
        self.url = url
        self.title = title
        self.chapters = chapters if chapters is not None else []
        logger.debug('Initialized manga %s (%s): %s', url,
                     'untitled' if title is None else title,
                     'No chapters' if chapters is None else str(len(chapters)))

    ##################################################
    # UPDATE
    ##################################################

    def fetch(self):
        """
        Fetch the manga HTML, parse it, and update the properties.
        Raises an error if the fetching or parsing failed.
        """
        soup = None
        logger.debug('Fetching manga HTML from %s...', self.url)
        response, err = Downloader.get(self.url)
        if err is not None:
            raise err
        logger.debug('Successfully fetched manga from %s...', self.url)

        logger.debug('Parsing manga into soup: %s...', self.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        logger.debug('Successfully parsed manga into soup: %s', self.url)

        self.updateWithSoup(soup)

    def updateWithSoup(self, soup):
        """
        Update the properties based on the manga's HTML soup.
        Raises an error if the parsing failed.

        Parameters:
            soup (BeautifulSoup): The manga's HTML soup.
        """
        # TODO - Change the implementation below to fit the specifics of your manga

        logger.debug('Updating manga properties (%s) based on soup...', self.url)

        # Get the title of the manga from its soup.
        title = Manga.getTitle(soup)

        # Get the chapter URLs. This may involve fetching other pages
        # if the main manga page doesn't contain all the chapter URLs.
        # The list should be in increasing order in terms of chapter number.
        chapters = Manga.getChapters(soup)

        # Update the properties
        self.title = title
        self.chapters = chapters

    def updateFromCache(self):
        """
        Update the fresh version (self) with the cached version from the JSON file.

        The manga may have been updated (e.g. added new chapters)
        since the last time the script was run. This will ensure
        that any new information will be included in the download.
        """
        # TODO Implement updateFromCache

    ##################################################
    # SAVE
    ##################################################

    def save(self, outputDir):
        """
        Save the manga as a JSON file.

        Parameters:
            outputDir (str): The output directory.
        """
        logger.debug('Saving to %s:  %s', outputDir, repr(self))
        # TODO Implement save

    ##################################################
    # REPRESENTATION
    ##################################################

    def __str__(self):
        result = ''
        result += f'URL: {self.url}\n'
        result += f'Title: {self.title}\n'
        if len(self.chapters) > 0:
            result += '\n'.join(f'{str(chapter)}\n' for chapter in self.chapters)
        else:
            result += '(No chapters)'
        return result

    def __repr__(self):
        title = 'Untitled' if self.title is None else self.title
        chapters = 'No chapters' if len(self.chapters) == 0 else f'{len(self.chapters)} chapters'
        return f'{self.url}  ({title})  ({chapters})'

    ##################################################
    # STATIC METHODS
    ##################################################

    @staticmethod
    def getTitle(soup):
        """
        Get the manga title from its soup.

        Parameters:
            soup (BeautifulSoup): The manga HTML soup.

        Returns:
            str: The title of the manga.
        """

        logger.debug('Parsing manga title from soup...')

        # TODO Implement manga-specific getTitle
        title = 'SampleMangaTitle'

        logger.debug("Parsed manga title '%s' from soup.", title)
        return title

    @staticmethod
    def getChapters(soup):
        """
        Get the manga chapters from its soup.

        Parameters:
            soup (BeautifulSoup): The manga HTML soup.

        Returns:
            list of Chapter: The list of Chapters of the manga.
        """

        logger.debug('Parsing manga chapters from soup...')

        # TODO Implement manga-specific getChapters

        chapterUrls = [
            'https://sample.com/chapter-1',
            'https://sample.com/chapter-2',
            'https://sample.com/chapter-3'
        ]

        # Instantiate a list of skeleton chapters (chapters containing only the url).
        chapters = []
        for idx, chapterUrl in enumerate(chapterUrls):
            chapters.append(Chapter(idx + 1, chapterUrl))

        logger.debug("Parsed %d chapters from soup.", len(chapters))
        return chapters
