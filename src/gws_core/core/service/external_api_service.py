# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict

import requests
from requests.models import Response


class ExternalApiService:
    """
    This class gives possibility to make http requests to external APIs

    """

    @classmethod
    def post(cls, url: str, body: Dict, headers: Dict[str, str] = None) -> Response:
        """
        Make an HTTP post request
        """
        if headers is None:
            headers = {}
        return requests.post(url, json=body, headers=headers)

    @classmethod
    def put(cls, url: str, body: Dict, headers: Dict[str, str] = None, files: Any = None) -> Response:
        """
        Make an HTTP put request
        """
        if headers is None:
            headers = {}
        return requests.put(url, json=body, headers=headers, files=files)

    @classmethod
    def put_form_data(cls, url: str, data: Dict, headers: Dict[str, str] = None, files: Any = None) -> Response:
        """
        Make an HTTP put request
        """
        if headers is None:
            headers = {}
        session = requests.Session()
        return session.put(url, data=data, headers=headers, files=files)

    @classmethod
    def get(cls, url: str, headers: Dict[str, str] = None) -> Response:
        """
        Make an HTTP get request
        """
        if headers is None:
            headers = {}
        return requests.get(url, headers=headers)

    @classmethod
    def delete(cls, url: str, headers: Dict[str, str] = None) -> Response:
        """
        Make an HTTP get request
        """
        if headers is None:
            headers = {}
        return requests.delete(url, headers=headers)
