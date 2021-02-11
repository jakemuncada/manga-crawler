"""
A model of a page of a manga.
"""

import os
import logging
import weakref

from downloader import Downloader


logger = logging.getLogger(__name__)


class Page:
    """
    The page of a manga.

    Attributes:
        chapter (Chapter): A weak reference to the chapter that this page belongs to.
        chapterNum (int): The numerical order of the chapter that this page belongs to.
        mangaTitle (str): The title of the manga.
        num (int): The numerical order of the page. Considered to be unique.
        pageUrl (str): The URL of the page HTML.
        imageUrl (str): The URL of the page image.
        filePath (str): The full path of the downloaded image.
        filename (str): The filename of the downloaded image.
        isDownloaded (bool): True if the page image has already been downloaded.
        isProcessed (bool): True if an attempt to download the image has been executed.
            This will always initialize to False whenever a Page is instantiated.
    """

    ################################################################################################
    # INITIALIZATION
    ################################################################################################

    def __init__(self, chapter, num, pageUrl, imageUrl=None,
                 filePath=None, filename=None, isDownloaded=False):
        self._chapter = weakref.ref(chapter)
        self.chapterNum = chapter.num
        self.mangaTitle = chapter.mangaTitle
        self.num = num
        self.pageUrl = pageUrl
        self.imageUrl = imageUrl
        self.filePath = filePath
        self.filename = filename
        self.isDownloaded = isDownloaded
        self.isProcessed = False

    @classmethod
    def fromJson(cls, chapter, jsonData):
        """
        Instantitate a Page from its JSON representation.

        Parameters:
            chapter (Chapter): The parent chapter who owns this page.
            jsonData (json): The JSON representation of the page.

        Returns:
            Page: The instantiated Page.
        """
        num = jsonData['num']
        pageUrl = jsonData['pageUrl']
        imageUrl = jsonData['imageUrl']
        filePath = jsonData['filePath']
        filename = jsonData['filename']
        isDownloaded = jsonData['isDownloaded']
        return cls(chapter, num, pageUrl, imageUrl, filePath, filename, isDownloaded)

    ################################################################################################
    # WEAK REF PROPERTIES
    ################################################################################################

    @property
    def chapter(self):
        """
        A weak reference to the parent chapter.
        Raises LookupError if parent is None.
        """
        if not self._chapter:
            raise LookupError("Parent chapter not found.")
        _chapter = self._chapter()
        if _chapter:
            return _chapter
        else:
            raise LookupError("Parent chapter was destroyed.")

    @property
    def manga(self):
        """
        A weak reference to the parent manga.
        Raises LookupError if parent is None.
        """
        return self.chapter.manga

    ################################################################################################
    # GETTERS
    ################################################################################################

    def getImageUrl(self, soup):
        """
        Get the image URL from its soup.

        Parameters:
            soup (BeautifulSoup): The page's HTML soup.

        Returns:
            str: The URL of the page image.
        """
        raise AssertionError('The image URL should already have been provided.')

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

    ################################################################################################
    # SETTERS
    ################################################################################################

    def setParent(self, chapter):
        """
        Set the chapter parent to a new Chapter object.

        Parameters:
            chapter (Chapter): The new chapter parent.
        """
        self._chapter = weakref.ref(chapter)
        self.mangaTitle = chapter.manga.title
        self.chapterNum = chapter.num

    ################################################################################################
    # UPDATE
    ################################################################################################

    def fetch(self):
        """
        Fetch the page HTML, parse it, and update the properties.
        Raises an error if the fetching or parsing failed.
        """
        raise AssertionError('The page does not have an HTML of its own, '
                             'it only consists of an image.')

    def updateWithSoup(self, soup):
        """
        Update the properties based on the page's HTML soup.
        Raises an error if the parsing failed.

        Parameters:
            soup (BeautifulSoup): The page's HTML soup.
        """
        raise AssertionError('The page does not have an HTML of its own, '
                             'it only consists of an image.')

    ################################################################################################
    # DOWNLOAD IMAGE
    ################################################################################################

    def downloadImage(self, outputDir):
        """
        Download the image and save it to the output directory.
        """
        logger.debug("Downloading image of '%s' Chapter %d Page %d (%s) as '%s'...",
                     self.mangaTitle, self.chapterNum, self.num,
                     self.imageUrl, self.filename)

        if self.imageUrl is None:
            raise AttributeError('Image URL not found.')

        if self.filename is None:
            self.filename = self.getImageFilename()

        mangaDirName = self.manga.directoryName
        chapterDirName = self.chapter.directoryName

        if mangaDirName is None:
            raise AttributeError('Manga directory name not found.')

        if chapterDirName is None:
            raise AttributeError('Chapter directory name not found.')

        outputDir = os.path.join(outputDir, mangaDirName, chapterDirName)

        outputPath = os.path.join(outputDir, self.filename)
        logger.debug("Output path for the image of '%s' Chapter %d Page %d is: %s",
                     self.mangaTitle, self.chapterNum, self.num, outputDir)

        os.makedirs(outputDir, exist_ok=True)

        err = Downloader.downloadImage(self.imageUrl, outputPath)
        if err is not None:
            raise err

        self.filePath = os.path.abspath(outputPath)
        self.isDownloaded = True

        logger.debug("Successfully downloaded image of '%s' Chapter %d Page %d to %s",
                     self.mangaTitle, self.chapterNum, self.num, self.filePath)

    ################################################################################################
    # REPRESENTATION
    ################################################################################################

    def __str__(self):
        return f'      Page {self.num}: {self.imageUrl}'

    def __repr__(self):
        imageUrl = 'No image URL' if self.imageUrl is None else self.imageUrl
        filename = 'No filename' if self.filename is None else self.filename
        return f'Page {self.num}: {imageUrl}  ({filename})  ({self.isDownloaded})'

    def toDict(self):
        """
        Returns the dictionary representation of the Page.
        """
        result = {
            'num': self.num,
            'pageUrl': self.pageUrl,
            'imageUrl': self.imageUrl,
            'filePath': self.filePath,
            'filename': self.filename,
            'isDownloaded': self.isDownloaded
        }
        return result
