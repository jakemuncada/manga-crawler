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

    def __init__(self, num, pageUrl, imageUrl=None, filePath=None,
                 filename=None, isDownloaded=False):
        self.num = num
        self.pageUrl = pageUrl
        self.imageUrl = imageUrl
        self.filePath = filePath
        self.filename = filename
        self.isDownloaded = isDownloaded

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

        Parameters:
            num (int): The page order number.
            imageUrl (str): The image URL.

        Returns:
            str: The filename for the image download file.
        """
        logger.debug('Getting filename of page %d (%s)...', self.num + 1, self.imageUrl)

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
        filename = f'{(self.num + 1):04}.{ext}'

        logger.debug("Filename of page %d (%s) is '%s'...", self.num + 1, self.imageUrl, filename)

        return filename

    ##################################################
    # UPDATE
    ##################################################

    def fetch(self):
        """
        Fetch the page HTML, parse it, and update the properties.
        Raises an error if the fetching or parsing failed.
        """
        soup = None
        logger.debug('Fetching page %d HTML from %s...', self.num, self.pageUrl)
        response, err = Downloader.get(self.pageUrl)
        if err is not None:
            raise err
        logger.debug('Successfully fetched page %d from %s...', self.num, self.pageUrl)

        logger.debug('Parsing page %d into soup...', self.num)
        soup = BeautifulSoup(response.text, 'html.parser')
        logger.debug('Successfully parsed page %d into soup.', self.num)

        self.updateWithSoup(soup)

    def updateWithSoup(self, soup):
        """
        Update the properties based on the page's HTML soup.
        Raises an error if the parsing failed.

        Parameters:
            soup (BeautifulSoup): The page's HTML soup.
        """
        # TODO - Change the implementation below to fit the specifics of your manga

        logger.debug('Updating page %d properties (%s) based on soup...', self.num, self.pageUrl)

        # Get the image URL
        imageUrl = Page.getImageUrl(soup)
        self.imageUrl = imageUrl

        # Get the filename for the download file (for later use)
        filename = self.getImageFilename()
        self.filename = filename

    ##################################################
    # DOWNLOAD IMAGE
    ##################################################

    def downloadImage(self, outputDir):
        """
        Download the image and save it to the output directory.
        """
        logger.debug("Downloading image of page %d (%s) as '%s'...",
                     self.num + 1, self.imageUrl, self.filename)

        if self.imageUrl is None:
            raise AttributeError('Image URL not found.')

        if self.filename is None:
            raise AttributeError('Image filename not found.')

        outputPath = os.path.join(outputDir, self.filename)
        logger.debug("Output path for '%s' (page %d) is: %s",
                     self.filename, self.num + 1, outputDir)

        err = Downloader.downloadImage(self.imageUrl, outputPath)
        if err is not None:
            raise err

        self.filePath = os.path.abspath(outputPath)
        self.isDownloaded = True

        logger.debug('Successfully downloaded page %d (%s) to %s',
                     self.num + 1, self.imageUrl, self.filePath)

    ##################################################
    # REPRESENTATION
    ##################################################

    def __str__(self):
        return f'      Page {self.num}: {self.imageUrl}'

    def __repr__(self):
        imageUrl = 'No image URL' if self.imageUrl is None else self.imageUrl
        filename = 'No filename' if self.filename is None else self.filename
        return f'Page {self.num}: {imageUrl}  ({filename})  ({self.isDownloaded})'

    ##################################################
    # STATIC METHODS
    ##################################################

    @staticmethod
    def getImageUrl(soup):
        """
        Get the image URL from its soup.

        Parameters:
            soup (BeautifulSoup): The page's HTML soup.

        Returns:
            str: The URL of the page image.
        """

        # TODO Move static method into instance method

        # TODO Implement manga-specific getImageUrl
        imageUrl = 'https://imgs.xkcd.com/comics/vaccine_ordering.png'

        logger.debug('Parsed image URL from soup: %s', imageUrl)

        return imageUrl
