import json
import os
from copy import copy

import requests
from requests import HTTPError

api_keys = os.getenv('YOUTUBE_API_KEYS', '').split(',')


class YoutubeObject:

    @staticmethod
    def get(endpoint, params):
        if os.getenv('DEBUG'):
            # Get from cached responses rather than API
            filename = f"{endpoint}_{'_'.join([f'{k}-{v}' for k, v in params.items()])}.json".replace("|", "")
            filepath = os.path.join('data', 'api-queries', filename)
            if os.path.exists(filepath):
                with open(filepath, "r") as queryfile:
                    response = json.loads(queryfile.read())
                    return response.get('items'), response.get('nextPageToken')

        print(f"Querying API for '{endpoint}' with parameters '{params}")
        base_url = os.getenv('YOUTUBE_API_URL', 'https://www.googleapis.com/youtube/v3/')

        auth_params = copy(params)  # Make a copy so the key doeesn't end up in logs
        auth_params['key'] = api_keys[0]
        response = requests.get(base_url + endpoint, params=auth_params)
        # If we still have multiple keys, try the next one
        if response.status_code == 403 and len(api_keys) > 1:
            api_keys.pop(0)
            return YoutubeObject.get(endpoint, params)
        elif response.status_code == 403:
            raise RuntimeError(response.json())
        elif response.status_code < 200 or response.status_code >= 400:
            raise HTTPError(response.json())
        if 'items' not in response.json() or len(response.json()['items']) == 0:
            raise HTTPError('API responded with no items')

        if os.getenv("DEBUG"):
            # Write responses to file cache
            with open(filepath, "w") as queryfile:
                queryfile.write(json.dumps(response.json(), indent=2))
        return response.json().get('items'), response.json().get('nextPageToken')
