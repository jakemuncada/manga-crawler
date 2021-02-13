"""
Provides high-level functions for fetching stuff from the internet.
"""

import shutil
import requests


class DownloaderError(Exception):
    """
    Errors related to the Downloader
    """


class Downloader:
    """
    Provides high-level functions for fetching stuff from the internet.
    """

    ################################################################################################
    # GET REQUEST
    ################################################################################################

    @staticmethod
    def get(url):
        """
        Send a GET request to the given URL.

        Parameters:
            url: The URL.

        Returns:
            response: The requests library response.
            error: The error that was generated. None if the request was successful.
        """

        response = None
        error = None

        try:
            # Fetch the data.
            response = requests.get(url)
            # Raise exception if any.
            response.raise_for_status()
            # If there were no exceptions, the download was successful.
        except Exception as err:  # pylint: disable=broad-except
            error = err

        return response, error

    ################################################################################################
    # DOWNLOAD IMAGE
    ################################################################################################

    @staticmethod
    def downloadImage(url, outputPath):
        """
        Download an image to the given path.

        Parameters:
            url (str): The image URL.
            outputPath (str): The full path (including filename) of the image.

        Returns:
            An exception if the download failed. None if the download was a success.
        """
        error = None
        try:
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                raise DownloaderError(f'Error: Status code {response.status_code}')
            with open(outputPath, 'wb') as outputFile:
                shutil.copyfileobj(response.raw, outputFile)
            del response
        except Exception as err:  # pylint: disable=broad-except
            error = err
        return error

    ################################################################################################
    # GET ERROR STRING
    ################################################################################################

    @staticmethod
    def getErrorString(err):
        """
        Get the description of the error.

        Parameters:
            err: The error.

        Returns:
            The description of the error.
        """
        desc = None
        try:
            raise err
        except requests.exceptions.HTTPError as err:
            desc = 'An HTTP error occurred.'
        except requests.exceptions.ProxyError as err:
            desc = 'A proxy error occurred.'
        except requests.exceptions.SSLError as err:
            desc = 'An SSL error occurred.'
        except requests.exceptions.ConnectTimeout as err:
            desc = 'The request timed out while trying to connect to the remote server.'
        except requests.exceptions.ReadTimeout as err:
            desc = 'The server did not send any data in the allotted amount of time.'
        except requests.exceptions.Timeout as err:
            desc = 'The request timed out.'
        except requests.exceptions.ConnectionError as err:
            desc = 'A Connection error occurred.'
        except requests.exceptions.URLRequired as err:
            desc = 'A valid URL is required to make a request.'
        except requests.exceptions.TooManyRedirects as err:
            desc = 'Too many redirects.'
        except requests.exceptions.MissingSchema as err:
            desc = 'The URL schema (e.g. http or https) is missing.'
        except requests.exceptions.InvalidSchema as err:
            desc = 'The URL schema is invalid.'
        except requests.exceptions.InvalidHeader as err:
            desc = 'The header value provided was somehow invalid.'
        except requests.exceptions.InvalidProxyURL as err:
            desc = 'The proxy URL provided is invalid.'
        except requests.exceptions.InvalidURL as err:
            desc = 'The URL provided was somehow invalid.'
        except Exception as err:  # pylint: disable=broad-except
            desc = 'An unexpected error occurred.'
            logger.excetion(err)
        return desc
