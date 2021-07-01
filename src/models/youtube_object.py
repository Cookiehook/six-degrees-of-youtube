import logging
import os
from copy import copy

import requests
from requests import HTTPError

logger = logging.getLogger()
api_keys = os.getenv('YOUTUBE_API_KEYS', '').split(',')


class YoutubeObject:
    """Base class for objects retrieved from the Youtube API"""

    @staticmethod
    def get(endpoint: str, params: dict) -> tuple:
        """
        Query the Youtube data API, and return the 'items' and 'nextPageToken'

        :param endpoint: Youtube endpoing to call. See https://developers.google.com/youtube/v3/docs
        :param params: Dictionary of parameters to send as a querystring
        :return: tuple of API items (dict) and pagination token (str)
        :raises: HTTPError if the API responds with non-20x response, or no items
        :raises: RuntimeError if an unrecoverable authentication error occurs
        """

        logger.info(f"Querying API with: '{endpoint}' - '{params}")
        base_url = os.getenv('YOUTUBE_API_URL', 'https://www.googleapis.com/youtube/v3/')

        auth_params = copy(params)  # Make a copy so the key doesn't end up in logs
        auth_params['key'] = api_keys[0]
        response = requests.get(base_url + endpoint, params=auth_params)

        # If we still have multiple keys, try the next one
        if response.status_code == 403 and len(api_keys) > 1:
            logger.warning("API quota limit reached, swapping key")
            api_keys.pop(0)
            return YoutubeObject.get(endpoint, params)

        # Unrecoverable errors. Raised for calling methods to handle
        message = f"Failed API call with: '{endpoint}' - '{params}'"
        if response.status_code == 403:
            logger.error(message)
            raise RuntimeError(response.json())
        elif response.status_code < 200 or response.status_code >= 400:
            logger.error(message)
            raise HTTPError(response.json())
        if 'items' not in response.json() or len(response.json()['items']) == 0:
            logger.error(message)
            raise HTTPError('API responded with no items')

        return response.json().get('items'), response.json().get('nextPageToken')
