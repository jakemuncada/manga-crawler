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

        self._killEvent = Event()  # Event that, if set, will trigger threads to terminate.
        self._endEvent = Event()  # Event that signifies that the last chapter has been processed
        # and that the program should end once the pageQueue is empty.

        self._failedChapters = Queue()  # The collection of chapters that failed to be processed.
        self._failedPages = Queue()  # The collection of pages that failed to be downloaded.

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

        self._failedChapters = Queue()  # The collection of chapters that failed to be processed.
        self._failedPages = Queue()  # The collection of pages that failed to be downloaded.

        logger.info('Start crawling through %d mangas...', len(self.mangaUrls))

        for mangaUrl in self.mangaUrls:
            if not self._killEvent.is_set():
                self._crawl(mangaUrl)

    def _crawl(self, mangaUrl):
        """
        Crawl through and download the given manga URL.
        Can be interrupted by Ctrl+C.
        """

        logger.info('Downloading manga: %s...', mangaUrl)

        # Fetch the manga and merge with the cached version
        self.fetchManga(mangaUrl)

        # Cannot continue to crawl if something went wrong while fetching manga
        if self.manga is None:
            return

        # Create the queues
        chapterQueue = Queue()
        pageQueue = Queue()

        # Create the chapter processor threads and the page downloader threads
        chapterThreads, pageThreads = self.startThreads(chapterQueue, pageQueue)

        # Wait until either the manga is finished downloading
        # or the user interrupts the process by pressing Ctrl + C.
        self.waitForCompletion(chapterThreads, pageThreads, pageQueue)

        # Print the list of chapters and pages that weren't downloaded
        self.displayUnsuccessfulItems()

        # Save the manga cache file
        self.saveManga()

    ################################################################################################
    # FETCH MANGA
    ################################################################################################

    def fetchManga(self, mangaUrl):
        """
        Fetch the manga to be processed and set it to `self.manga`.
        If something went wrong while fetching the manga, `self.manga` will be None.

        The manga will also be compared to its cached version,
        so that previously downloaded chapters and pages will not be downloaded again.

        However, the manga might have been updated (new chapters added),
        so those will also be added to the chapter list so they can be downloaded.

        Parameters:
            mangaUrl (str): The manga URL.
        """

        # First, set the manga to None
        self.manga = None

        # Instantiate a freshly fetched manga
        try:
            self.manga = Manga(mangaUrl)
            self.manga.fetch()
        except Exception as err:  # pylint: disable=broad-except
            logger.error('Failed to fetch manga %s, %s', mangaUrl, err)
            return

        # Compare the freshly fetched manga from the cached version.

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

    ################################################################################################
    # START THREADS
    ################################################################################################

    def startThreads(self, chapterQueue, pageQueue):
        """
        Start the chapter processor threads and the page downloader threads.

        Parameters:
            chapterQueue (Queue of Chapter): The queue containing the chapters to be processed.
            pageQueue (Queue of Page): The queue containing the pages to be downloaded.

        Returns:
            (list, list): The chapter processor thread list and the page downloader thread list.
        """

        # Populate the chapter queue
        for chapter in self.manga.chapters:
            chapterQueue.put(chapter)

        logger.info("The manga '%s' has %d chapters. Downloading...",
                    self.manga.title, len(self.manga.chapters))

        # Start the chapter downloader threads
        _chapterThreads = []
        for idx in range(self.chapterThreadCount):
            threadName = f'ChapterDownloaderThread{idx+1}'
            t = Thread(name=threadName, target=self.chapterWorker,
                       args=(threadName, chapterQueue, pageQueue))
            _chapterThreads.append(t)
            t.start()

        # Start the page downloader threads
        _pageThreads = []
        for _ in range(self.pageThreadCount):
            threadName = f'PageDownloaderThread{idx+1}'
            t = Thread(name=threadName, target=self.pageWorker,
                       args=(threadName, pageQueue))
            _pageThreads.append(t)
            t.start()

        return _chapterThreads, _pageThreads

    ################################################################################################
    # WAIT FOR COMPLETION
    ################################################################################################

    def waitForCompletion(self, chapterThreads, pageThreads, pageQueue):
        """
        Wait until the manga has finished downloading or the user interrupts the process
        by pressing Ctrl + C.

        Parameters:
            chapterThreads (list of Thread): The list of chapter processor threads.
            pageThreads (list of Thread): The list of page downloader threads.
            pageQueue (Queue of Page): The queue containing the pages to be downloaded.
        """

        try:
            # Wait until both chapterQueue and pageQueue are empty
            while not self._endEvent.is_set() or not pageQueue.empty():
                sleep(0.3)

            # Wait for all the threads to finish
            logger.debug('Nearly done... Waiting for the last download threads to finish...')
            for t in chapterThreads:
                logger.debug('Waiting for %s...', t.name)
                t.join()
            for t in pageThreads:
                logger.debug('Waiting for %s...', t.name)
                t.join()

            logger.info('Finished downloading %s.', self.manga.title)

        except KeyboardInterrupt:
            # If Ctrl+C is pressed by the user, send a kill signal
            # and wait for the threads to finish.
            logger.debug('Keyboard interrupt detected.')
            self.stop(chapterThreads, pageThreads)

    ################################################################################################
    # PROCESS CHAPTER
    ################################################################################################

    def processChapter(self, chapter, pageQueue):
        """
        Download and parse the chapter HTML and update the chapter info.

        This will update the chapter title and create the list of Pages.
        These pages will then be added onto the pageQueue so they can be downloaded.

        Parameters:
            chapter (Chapter): The chapter to be processed.
            pageQueue (Queue of Page): The queue containing the pages to be downloaded.
        """
        # If all the pages of the chapter have been downloaded, there is nothing to do here
        if chapter.isDownloaded:
            logger.debug("Skipping '%s' chapter %d...", chapter.mangaTitle, chapter.num)
            return

        logger.info("Processing '%s' chapter %d...", chapter.mangaTitle, chapter.num)

        # Fetch the chapter HTML and update its properties
        # only if its pages list is empty or if the title isn't set.
        if len(chapter.pages) == 0 or chapter.title is None:
            try:
                chapter.fetch()
                chapterReady = True
            except Exception as err:  # pylint: disable=broad-except
                logger.error("Failed to fetch '%s' chapter %d (%s), %s",
                             chapter.mangaTitle, chapter.num, chapter.url, err)
                logger.exception(err)
                chapterReady = False
                self._failedChapters.put(chapter)
        else:
            # If the chapter's title is set and it already has pages in its page list,
            # we can process those without re-fetching the chapter.
            chapterReady = True

        if chapterReady:
            # Put all the pages in the pageQueue
            for page in chapter.pages:
                logger.debug("Adding '%s' page %d of chapter %d to the page queue.",
                             page.mangaTitle, page.num, chapter.num)
                pageQueue.put(page)

            # Save the manga cache file
            self.saveManga()

    def chapterWorker(self, threadName, chapterQueue, pageQueue):
        """
        Work function of the chapter threads which contains the loop
        that continues until all the chapters in the chapter queue have been processed.
        (Or until the user interrupts by pressing Ctrl + C.)

        Parameters:
            threadName (str): The thread name.
            chapterQueue (Queue of Chapter): The queue containing the chapters to be processed.
            pageQueue (Queue of Page): The queue containing the pages to be downloaded.
        """
        # Loop until all the chapters in the queue have been processed
        while not chapterQueue.empty():

            # If the kill event is set, terminate the thread
            if self._killEvent.is_set():
                logger.debug('Kill event is set, terminating %s...', threadName)
                break

            # Get the next chapter in the queue
            chapter = chapterQueue.get()

            # Process the chapter
            self.processChapter(chapter, pageQueue)

            # Now that the chapter has been processed, check if the chapterQueue is empty
            if chapterQueue.empty():
                logger.debug('Chapter queue is empty, setting end event...')
                # If the queue is empty, tell the crawler that the manga is finished downloading
                # once all the pages in the page queue are downloaded.
                self._endEvent.set()

            # Notify the queue that the chapter is done processing
            chapterQueue.task_done()

    ################################################################################################
    # PROCESS PAGE
    ################################################################################################

    def pageWorker(self, threadName, pageQueue):
        """
        Work function of the page threads which contains the loop
        that continues until all the pages in the page queue have been processed.
        (Or until the user interrupts by pressing Ctrl + C.)

        Parameters:
            threadName (str): The thread name.
            pageQueue (Queue of Page): The queue containing the pages to be downloaded.
        """
        # The page thread will end if the endEvent is set and the pageQueue is empty
        while not self._endEvent.is_set() or not pageQueue.empty():

            # If the kill event is set, terminate the thread
            if self._killEvent.is_set():
                logger.debug('Kill event is set, terminating %s...', threadName)
                break

            # If the pageQueue is empty, do nothing
            if not pageQueue.empty():
                page = pageQueue.get()
                self.processPage(page)
                pageQueue.task_done()

    def processPage(self, page):
        """
        Download the page image and update the page info.

        Parameters:
            page (Page): The page to be downloaded.
        """
        # If the page has already been downloaded, there is nothing to do here
        if page.isDownloaded:
            logger.debug("Skipping '%s' chapter %d page %d...",
                         page.mangaTitle, page.chapterNum, page.num)
            return

        logger.debug("Processing '%s' chapter %d page %d...",
                     page.mangaTitle, page.chapterNum, page.num)

        try:
            # Try to download the image
            page.downloadImage(self.outputDir)
        except Exception as err:  # pylint: disable=broad-except
            logger.error("Failed to download image: '%s' page %d of chapter %d (%s), %s",
                         page.mangaTitle, page.num, page.chapterNum, page.imageUrl, err)
            self._failedPages.put(page)

    ################################################################################################
    # STOP
    ################################################################################################

    def stop(self, chapterThreads, pageThreads):
        """
        Stop the crawling process.

        Parameters:
            chapterThreads (list of Thread): The list of chapter processor threads.
            pageThreads (list of Thread): The list of page downloader threads.
        """
        if self.isCrawling:
            self.isCrawling = False

            logger.info('Stopping threads... Please wait for active threads to finish...')
            self._killEvent.set()

            for t in chapterThreads:
                logger.debug('%s is terminating...', t.name)
                t.join()
            for t in pageThreads:
                logger.debug('%s is terminating...', t.name)
                t.join()

    ################################################################################################
    # PRINT FAILURES
    ################################################################################################

    def displayUnsuccessfulItems(self):
        """
        Display the chapters and pages that failed to be fetched.
        """
        if self._failedChapters.empty() and self._failedPages.empty():
            logger.info('All chapters and pages were fetched successfully.')
            return

        logger.info('The following were fetched unsuccessfully:')

        if not self._failedChapters.empty():
            while not self._failedChapters.empty():
                chapter = self._failedChapters.get()
                logger.info("Chapter %d of '%s': %s", chapter.num, chapter.mangaTitle, chapter.url)

        if not self._failedPages.empty():
            while not self._failedPages.empty():
                page = self._failedPages.get()
                logger.info("Page %d of Chapter %d of '%s': %s",
                            page.num, page.chapterNum, page.mangaTitle, page.url)

    ################################################################################################
    # SAVE MANGA
    ################################################################################################

    def saveManga(self):
        """
        Save the manga to its JSON cache file.
        """
        try:
            self.manga.save(self.outputDir)
        except Exception as err:  # pylint: disable=broad-except
            logger.error("Failed to save '%s' cache file, %s", self.manga.title, err)
