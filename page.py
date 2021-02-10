"""
A model of a page of a manga.
"""

import os
import logging
from bs4 import BeautifulSoup

from downloader import Downloader


logger = logging.getLogger(__name__)


class Page:
    """
    The page of a manga.

    Attributes:
        mangaTitle (str): The title of the manga.
        chapterNum (int): The order number of the chapter that this page belongs to.
        num (int): The numerical order of the chapter. Considered to be unique.
        pageUrl (str): The URL of the page HTML.
        imageUrl (str): The URL of the page image.
        filePath (str): The full path of the downloaded image.
        filename (str): The filename of the downloaded image.
        isDownloaded (bool): True if the page image has already been downloaded.
    """

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self, mangaTitle, chapterNum, num, pageUrl, imageUrl=None,
                 filePath=None, filename=None, isDownloaded=False):
        self.mangaTitle = mangaTitle
        self.chapterNum = chapterNum
        self.num = num
        self.pageUrl = pageUrl
        self.imageUrl = imageUrl
        self.filePath = filePath
        self.filename = filename
        self.isDownloaded = isDownloaded

    ##################################################
    # GETTERS
    ##################################################

    def getImageUrl(self, soup):
        """
        Get the image URL from its soup.

        Parameters:
            soup (BeautifulSoup): The page's HTML soup.

        Returns:
            str: The URL of the page image.
        """

        logger.debug('Parsing image URL of Chapter %d Page %d from soup...',
                     self.chapterNum, self.num)

        # TODO Implement manga-specific getImageUrl
        imageUrl = 'https://imgs.xkcd.com/comics/vaccine_ordering.png'

        logger.debug('Parsed image URL of Chapter %d Page %d from soup: %s',
                     self.chapterNum, self.num, imageUrl)

        return imageUrl

    ##################################################
    # UPDATE
    ##################################################

    def getImageFilename(self):
        """
        Get the filename for the image download file.

        Note:
            - The image URL must not be None.
            - The image URL must not end with a '/'.
            - The image URL must end with the image's extension type (.png, .jpg, .jpeg).

        Returns:
            str: The filename for the image download file.
        """

        logger.debug('Getting filename of Chapter %d Page %d (%s)...',
                     self.chapterNum, self.num, self.imageUrl)

        # Check that the image URL is not None
        if self.imageUrl is None:
            raise AttributeError('Image URL not found.')

        if '.' not in self.imageUrl:
            raise ValueError('Image URL is not a valid image type.')

        # Get the image extension from the image URL
        ext = self.imageUrl.rsplit('.', 1)[-1]

        # Check that the extension is a valid image type
        validExts = ['png', 'jpg', 'jpeg']
        if ext not in validExts:
            raise ValueError('Image URL is not a valid image type.')

        # Filename is the order number as a 4-digit number with the valid extension
        filename = f'{(self.num):04}.{ext}'

        logger.debug("Filename of Chapter %d Page %d is '%s'...",
                     self.chapterNum, self.num, filename)

        return filename

    ##################################################
    # UPDATE
    ##################################################

    def fetch(self):
        """
        Fetch the page HTML, parse it, and update the properties.
        Raises an error if the fetching or parsing failed.
        """

        logger.debug("Fetching '%s' Chapter %d Page %d HTML from %s...",
                     self.mangaTitle, self.chapterNum, self.num, self.pageUrl)

        soup = None

        # Send HTTP request to get page HTML
        response, err = Downloader.get(self.pageUrl)
        # If the HTTP request failed, raise the error
        if err is not None:
            raise err

        logger.debug("Successfully fetched '%s' Chapter %d Page %d from %s...",
                     self.mangaTitle, self.chapterNum, self.num, self.pageUrl)

        logger.debug("Parsing '%s' Chapter %d Page %d into soup...",
                     self.mangaTitle, self.chapterNum, self.num)
        soup = BeautifulSoup(response.text, 'html.parser')
        logger.debug("Successfully parsed '%s' Chapter %d Page %d into soup.",
                     self.mangaTitle, self.chapterNum, self.num)

        self.updateWithSoup(soup)

    def updateWithSoup(self, soup):
        """
        Update the properties based on the page's HTML soup.
        Raises an error if the parsing failed.

        Parameters:
            soup (BeautifulSoup): The page's HTML soup.
        """
        # TODO - Change the implementation below to fit the specifics of your manga

        logger.debug("Updating '%s' Chapter %d Page %d based on soup...",
                     self.mangaTitle, self.chapterNum, self.num)

        # Get the image URL
        imageUrl = self.getImageUrl(soup)
        self.imageUrl = imageUrl

        # Get the filename for the download file (for later use)
        filename = self.getImageFilename()
        self.filename = filename

        logger.debug("Updated '%s' Chapter %d Page %d.",
                     self.mangaTitle, self.chapterNum, self.num)

    ##################################################
    # DOWNLOAD IMAGE
    ##################################################

    def downloadImage(self, outputDir):
        """
        Download the image and save it to the output directory.
        """
        logger.debug("Downloading image of '%s' Chapter %d Page %d (%s) as '%s'...",
                     self.mangaTitle, self.chapterNum, self.num, self.imageUrl, self.filename)

        if self.imageUrl is None:
            raise AttributeError('Image URL not found.')

        if self.filename is None:
            raise AttributeError('Image filename not found.')

        outputPath = os.path.join(outputDir, self.filename)
        logger.debug("Output path for the image of '%s' Chapter %d Page %d is: %s",
                     self.mangaTitle, self.chapterNum, self.num, outputDir)

        err = Downloader.downloadImage(self.imageUrl, outputPath)
        if err is not None:
            raise err

        self.filePath = os.path.abspath(outputPath)
        self.isDownloaded = True

        logger.debug("Successfully downloaded image of '%s' Chapter %d Page %d to %s",
                     self.mangaTitle, self.chapterNum, self.num, self.filePath)

    ##################################################
    # REPRESENTATION
    ##################################################

    def __str__(self):
        return f'      Page {self.num}: {self.imageUrl}'

    def __repr__(self):
        imageUrl = 'No image URL' if self.imageUrl is None else self.imageUrl
        filename = 'No filename' if self.filename is None else self.filename
        return f'Page {self.num}: {imageUrl}  ({filename})  ({self.isDownloaded})'
