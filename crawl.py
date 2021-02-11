"""
Class that provides the functionality to crawl a manga.
"""

import os
import logging
from time import sleep
from queue import Queue
from threading import Thread, Event

from manga import Manga


logger = logging.getLogger(__name__)


class MangaCrawler:
    """
    Class that provides the functionality to crawl a manga.

    Parameters:
        mangaUrls (list of str): The list of manga URLs to crawl.
        chapterThreadCount (int): The number of chapter download threads.
        pageThreadCount (int): The number of page download threads.
        outputDir (str): The output directory.
    """

    ################################################################################################
    # INITIALIZATION
    ################################################################################################

    def __init__(self, mangaUrls, chapterThreadCount, pageThreadCount, outputDir):
        self.mangaUrls = mangaUrls
        self.chapterThreadCount = chapterThreadCount
        self.pageThreadCount = pageThreadCount
        self.outputDir = outputDir

        self.isCrawling = False  # True if the crawling process is currently ongoing.
        self.manga = None  # The manga currently being crawled

        self._chapterThreads = []  # List of the chapter downloader threads.
        self._pageThreads = []  # List of the page downloader threads.

        self._chapterQueue = Queue()  # Queue of chapters to be processed.
        self._pageQueue = Queue()  # Queue of pages to be downloaded.

        self._killEvent = Event()  # Event that, if set, will trigger threads to terminate.
        self._endEvent = Event()  # Event that signifies that the last chapter has been processed
        # and that the program should end once the pageQueue is empty.

        self._failedUrls = Queue()  # The collection of URLs that failed to be downloaded.

    ################################################################################################
    # CRAWL
    ################################################################################################

    def crawl(self):
        """
        Crawl through and download all of the manga URLs in the list, one by one.
        Can be interrupted by Ctrl+C.
        """
        self.isCrawling = True

        self._killEvent = Event()  # If set, will trigger threads to terminate.
        self._endEvent = Event()  # Event that signifies that the last chapter
        # has been processed and that the program should end once the pageQueue is empty.

        logger.debug('Start crawling through %d mangas...', len(self.mangaUrls))

        for mangaUrl in self.mangaUrls:

            self._chapterThreads = []  # List of the chapter downloader threads.
            self._pageThreads = []  # List of the page downloader threads.

            self._chapterQueue = Queue()  # Queue of chapters to be processed.
            self._pageQueue = Queue()  # Queue of pages to be downloaded.

            self._failedUrls = Queue()  # The collection of URLs that failed to be downloaded.

            if not self._killEvent.is_set():
                self._crawl(mangaUrl)

    def _crawl(self, mangaUrl):
        """
        Crawl through and download the given manga URL.
        Can be interrupted by Ctrl+C.
        """

        logger.info('Downloading manga: %s...', mangaUrl)

        # Instantiate a freshly fetched manga
        try:
            self.manga = Manga(mangaUrl)
            self.manga.fetch()
        except Exception as err:  # pylint: disable=broad-except
            logger.error('Failed to fetch manga %s, %s', mangaUrl, err)
            return

        # Compare the freshly fetched manga from the cached version.
        # The manga might have been updated (new chapters added),
        # so we include that in the cached version.

        # On the other hand, we do not want to download the chapters again
        # if they have already been downloaded before.

        cachePath = os.path.join(self.outputDir, self.manga.directoryName, 'cache.json')
        if os.path.exists(cachePath):
            logger.info('Loading previous download info of %s...', self.manga.title)
            try:
                self.manga.updateFromCache(cachePath)
                logger.info("Manga '%s' has been updated from the cache.", self.manga.title)
            except Exception as err:  # pylint: disable=broad-except
                logger.error("Failed to retrieve previous download info about '%s', %s",
                             self.manga.title, err)
        else:
            logger.info('No previous information about %s exists in cache.', self.manga.title)

        # Populate the chapter queue
        for chapter in self.manga.chapters:
            self._chapterQueue.put(chapter)

        logger.info("The manga '%s' has %d chapters. Downloading...",
                    self.manga.title, len(self.manga.chapters))

        # Start the chapter downloader threads
        for idx in range(self.chapterThreadCount):
            threadName = f'ChapterDownloaderThread{idx+1}'
            t = Thread(name=threadName, target=self.processChapter, args=(threadName,))
            self._chapterThreads.append(t)
            t.start()

        # Start the page downloader threads
        for _ in range(self.pageThreadCount):
            threadName = f'PageDownloaderThread{idx+1}'
            t = Thread(name=threadName, target=self.processPage, args=(threadName,))
            self._pageThreads.append(t)
            t.start()

        try:
            # Wait until both chapterQueue and pageQueue are empty
            while not self._endEvent.is_set() or not self._pageQueue.empty():
                sleep(0.3)

            # Wait for all the threads to finish
            logger.debug('Nearly done... Waiting for the last download threads to finish...')
            for t in self._chapterThreads:
                logger.debug('Waiting for %s...', t.name)
                t.join()
            for t in self._pageThreads:
                logger.debug('Waiting for %s...', t.name)
                t.join()

            logger.info('Finished downloading %s.', self.manga.title)

        except KeyboardInterrupt:
            # If Ctrl+C is pressed by the user, send a kill signal
            # and wait for the threads to finish.
            logger.debug('Keyboard interrupt detected.')
            self.stop()

        # Print the list of URLs that weren't downloaded
        if not self._failedUrls.empty():
            logger.info('Failed to download the following:')
            while not self._failedUrls.empty():
                logger.info('   %s', self._failedUrls.get())
        else:
            logger.debug('All URLs were successfully fetched with no failures.')

        try:
            # Save the manga as a JSON file
            self.manga.save(self.outputDir)
        except Exception as err:  # pylint: disable=broad-except
            logger.error("Failed to save '%s' JSON cache, %s", self.manga.title, err)

    ################################################################################################
    # PROCESS CHAPTER
    ################################################################################################

    def processChapter(self, threadName):
        """
        Download and parse the chapter HTML and update the chapter info.

        This will update the chapter title and create the list of Pages.
        These pages will then be added onto the pageQueue so they can be downloaded.

        Parameters:
            threadName (str): The thread name.
        """
        # Loop until all the chapters in the queue have been processed
        while not self._chapterQueue.empty():

            # If the kill event is set, terminate the thread
            if self._killEvent.is_set():
                logger.debug('Kill event is set, terminating %s...', threadName)
                break

            chapter = self._chapterQueue.get()

            # Process the chapter only if it hasn't been downloaded
            # i.e. all of its pages have been downloaded already.
            if not chapter.isDownloaded:

                logger.info('Processing chapter %d...', chapter.num)

                # Fetch the chapter HTML and update its properties
                # only if its pages list is empty or if the title isn't set.
                if len(chapter.pages) == 0 or chapter.title is None:
                    try:
                        chapter.fetch()
                        chapterReady = True
                    except Exception as err:  # pylint: disable=broad-except
                        logger.error("Failed to fetch chapter %s of '%s', %s",
                                     chapter.url, self.manga.title, err)
                        logger.exception(err)
                        chapterReady = False
                        self._failedUrls.put(chapter.url)
                else:
                    # If the chapter already has pages in its list,
                    # we can process those without fetching the chapter.
                    chapterReady = True

                if chapterReady:
                    # Put all the pages in the pageQueue
                    for page in chapter.pages:
                        logger.debug('Adding page %d of chapter %d to the page queue.',
                                     page.num, chapter.num)
                        self._pageQueue.put(page)

                    try:
                        # Save the manga as a JSON file
                        self.manga.save(self.outputDir)
                    except Exception as err:  # pylint: disable=broad-except
                        logger.error("Failed to save '%s' JSON cache, %s",
                                     self.manga.title, err)

            # Otherwise, do not process the chapter if all its pages have been downloaded already
            else:
                logger.info("Skipping chapter %d...",
                            chapter.num)

            # If the chapterQueue is empty, set the endEvent
            if self._chapterQueue.empty():
                logger.debug('Chapter queue is empty, setting end event...')
                self._endEvent.set()

            self._chapterQueue.task_done()

    ################################################################################################
    # PROCESS PAGE
    ################################################################################################

    def processPage(self, threadName):
        """
        Download the page image and update the page info.

        Parameters:
            threadName (str): The thread name.
        """
        # The page thread will end if the endEvent is set and the pageQueue is empty
        while not self._endEvent.is_set() or not self._pageQueue.empty():

            # If the kill event is set, terminate the thread
            if self._killEvent.is_set():
                logger.debug('Kill event is set, terminating %s...', threadName)
                break

            # If the pageQueue is empty, do nothing
            if not self._pageQueue.empty():
                page = self._pageQueue.get()

                # Process the page only if it hasn't been downloaded
                if not page.isDownloaded:

                    logger.info('Processing page %d of chapter %d...', page.num, page.chapter.num)

                    # Download the image if the fetch block above did not raise an exception
                    try:
                        page.downloadImage(self.outputDir)
                    except Exception as err:  # pylint: disable=broad-except
                        logger.error('Failed to download image of page %d: %s, %s',
                                     page.num, page.imageUrl, err)

                # Otherwise, skip the page if it has already been downloaded
                else:
                    logger.info("Skipping page %d of chapter %d...",
                                page.num, page.chapter.num)

                self._pageQueue.task_done()

    def stop(self):
        """
        Stop the crawling process.
        """
        if self.isCrawling:
            self.isCrawling = False

            logger.info('Stopping threads... Please wait for active threads to finish...')
            self._killEvent.set()

            for t in self._chapterThreads:
                logger.debug('%s is terminating...', t.name)
                t.join()
            for t in self._pageThreads:
                logger.debug('%s is terminating...', t.name)
                t.join()
