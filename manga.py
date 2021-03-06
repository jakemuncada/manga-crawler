"""
A model of the manga to be downloaded.
"""

import os
import json
import logging
from threading import Lock
from bs4 import BeautifulSoup

from chapter import Chapter
from downloader import Downloader
from impl import getSampleTitle, getSampleChapterUrls


logger = logging.getLogger(__name__)


class Manga:
    """
    The manga to be downloaded.

    Attributes:
        url (str): The URL of the main manga page.
        title (str): The title of the manga.
        chapters (list of Chapter): List of the chapters of the manga.
    """

    ################################################################################################
    # INITIALIZATION
    ################################################################################################

    def __init__(self, url, title=None, chapters=None):
        self.url = url
        self.title = title
        self.chapters = chapters if chapters is not None else []

        self._directoryName = None  # Cache of the directoryName property
        self._cacheLock = Lock()  # Lock for thread-safe saving of JSON cache

        logger.debug('Initialized manga %s (%s): %s', url,
                     'untitled' if title is None else title,
                     'No chapters' if chapters is None else str(len(chapters)))

    @classmethod
    def fromCache(cls, cacheFilePath):
        """
        Instantitate a Manga from its JSON cache file.

        Parameters:
            cacheFilePath (str): The full path of the JSON cache file.

        Returns:
            Manga: The instantiated Manga.
        """

        logger.debug('Loading cache file: %s...', cacheFilePath)

        if not os.path.exists(cacheFilePath):
            raise IOError(f'JSON cache ({cacheFilePath}) not found.')

        with open(cacheFilePath, 'r') as inputFile:
            jsonData = json.load(inputFile)
            logger.debug('Cache file loaded and parsed to JSON successfully: %s', cacheFilePath)
            return Manga.fromJson(jsonData)

    @classmethod
    def fromJson(cls, jsonData):
        """
        Instantitate a Manga from its JSON representation.

        Parameters:
            jsonData (json): The JSON representation of the Manga.

        Returns:
            Manga: The instantiated Manga.
        """
        logger.debug('Instantiating a Manga from its JSON representation...')

        url = jsonData['url']
        title = jsonData['title']

        # Instantiate the manga without chapters for now
        manga = cls(url, title)

        # Instantiate the chapters by passing the manga
        chapters = [Chapter.fromJson(manga, chapter) for chapter in jsonData['chapters']]
        manga.chapters = chapters

        return manga

    ################################################################################################
    # PROPERTIES
    ################################################################################################

    @property
    def directoryName(self):
        """
        The directory name, which is a Windows file-safe version of the manga title.
        None if the title is None.
        """
        if self.title is None:
            self._directoryName = None
            return None

        if self._directoryName is not None:
            return self._directoryName

        logger.debug("Converting manga title (%s) to manga directory name...", self.title)

        mangaDirName = self.title
        invalidFilenameChars = '<>:"/\\|?*.'
        for invalidChar in invalidFilenameChars:
            mangaDirName = mangaDirName.replace(invalidChar, '_')

        self._directoryName = mangaDirName

        logger.debug("Directory name of Manga '%s' is '%s'.", self.title, self._directoryName)
        return self._directoryName

    ################################################################################################
    # GETTERS
    ################################################################################################

    def getTitle(self, soup):
        """
        Get the manga title from its soup.

        Parameters:
            soup (BeautifulSoup): The manga HTML soup.

        Returns:
            str: The title of the manga.
        """

        logger.debug('Parsing manga title from soup (%s)...', self.url)

        ##################################################
        # Site-specific implementation
        ##################################################
        title = getSampleTitle(soup)
        ##################################################

        if title is None or title == '':
            raise ValueError('Manga title is invalid: "%s".')

        logger.debug("Parsed manga title '%s' from soup.", title)
        return title

    def getChapters(self, soup):
        """
        Get the manga chapters from its soup.

        Parameters:
            soup (BeautifulSoup): The manga HTML soup.

        Returns:
            list of Chapter: The list of Chapters of the manga.
        """

        logger.debug('Parsing manga chapters from soup (%s)...', self.url)

        chapterUrls = []

        ##################################################
        # Site-specific implementation
        ##################################################
        chapterUrls = getSampleChapterUrls(soup)
        ##################################################

        # Instantiate a list of skeleton chapters (chapters containing only the url).
        chapters = []
        for idx, chapterUrl in enumerate(chapterUrls):
            chapterNum = idx + 1
            chapterTitle = f'Chapter {chapterNum:03}'
            chapters.append(Chapter(self, chapterNum, chapterUrl, chapterTitle))

        logger.debug("Parsed %d chapters from soup (%s).", len(chapters), self.url)
        return chapters

    ################################################################################################
    # UPDATE
    ################################################################################################

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

        logger.debug('Updating manga properties (%s) based on soup...', self.url)

        # Get the title of the manga from its soup.
        title = self.getTitle(soup)
        self.title = title

        # Get the chapter URLs. This may involve fetching other pages
        # if the main manga page doesn't contain all the chapter URLs.
        # The list should be in increasing order in terms of chapter number.
        chapters = self.getChapters(soup)
        self.chapters = chapters

        logger.debug("Manga '%s' (%s) has been updated.", self.title, self.url)

    def updateFromCache(self, cachePath):
        """
        Update the fresh version (self) with the cached version from the JSON file.

        The manga may have been updated (e.g. added new chapters)
        since the last time the script was run. This will ensure
        that any new information will be included in the download.

        Parameters:
            cachePath (str): The full path of the manga cache file.

        Raises:
            IOError: If the cache file does not exist or failed to be parsed.

        """

        logger.debug('Loading cached manga from %s...', cachePath)
        cachedManga = Manga.fromCache(cachePath)
        logger.debug("Cached version of '%s' has been loaded successfully.", self.title)

        # Update the title
        self.title = cachedManga.title

        # For every chapter in the fresh version, if it exists in the cache,
        # set its information to be equal that of the cache.
        for freshChapter in self.chapters:
            for cachedChapter in cachedManga.chapters:
                if freshChapter.num == cachedChapter.num:
                    freshChapter.url = cachedChapter.url
                    freshChapter.title = cachedChapter.title
                    freshChapter.pages = cachedChapter.pages
                    break

        # For every chapter in the cached version, if it does NOT exist in the fresh version,
        # add it to the list of chapters of the fresh manga.
        for cachedChapter in cachedManga.chapters:
            # Check if the cached chapter does not exist in the fresh manga
            if not any([freshChapter.num == cachedChapter.num for freshChapter in self.chapters]):
                self.chapters.append(cachedChapter)

        # Finally, sort the chapters according to the order number
        self.chapters.sort(key=lambda chapter: chapter.num)

        # Update the parent-links of all chapters and pages
        for chapter in self.chapters:
            chapter.setParent(self)
            for page in chapter.pages:
                page.setParent(chapter)

        logger.debug("Successfully updated '%s' from its cache.", self.title)

    ################################################################################################
    # SAVE
    ################################################################################################

    def save(self, outputDir):
        """
        Save the manga as a JSON file.

        Parameters:
            outputDir (str): The output directory.
        """
        logger.debug("Saving JSON cache to %s: %s", outputDir, repr(self))

        self._cacheLock.acquire()

        try:
            if self.directoryName is None:
                raise AttributeError('Directory name not found.')

            outputDir = os.path.join(outputDir, self.directoryName)
            filePath = os.path.join(outputDir, 'cache.json')

            os.makedirs(outputDir, exist_ok=True)

            with open(filePath, 'w') as writer:
                jsonStr = json.dumps(self.toDict(), indent=4)
                writer.write(jsonStr)
                logger.debug("Saved JSON cache of '%s' to: %s", self.title, filePath)
        except:
            self._cacheLock.release()
            raise
        else:
            self._cacheLock.release()

    ################################################################################################
    # REPRESENTATION
    ################################################################################################

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

    def toDict(self):
        """
        Returns the dictionary representation of the Manga.
        """
        result = {
            'url': self.url,
            'title': self.title,
            'chapters': [chapter.toDict() for chapter in self.chapters]
        }
        return result
