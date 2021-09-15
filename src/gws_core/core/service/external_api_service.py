# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict

import requests
from requests.models import Response


class ExternalApiService:
    """
    This class gives possibility to make http requests to external APIs

    """

    @classmethod
    def post(cls, url: str, body: Dict) -> Response:
        """
        Make an HTTP post request
        """
        return requests.post(url, data=body)

    @classmethod
    def get(cls, url: str, headers: Dict[str, str] = None) -> Response:
        """
        Make an HTTP get request
        """
        if headers is None:
            headers = {}
        return requests.get(url, headers=headers)
