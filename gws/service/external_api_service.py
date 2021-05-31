from typing import Dict
import requests
from requests.models import Response



class ExternalApiService:
    """
    This class give possibility to make http request to external api

    """

    @classmethod
    def post(cls, url: str, body: Dict) -> Response:
        """
        Make an HTTP post request
        """
        return requests.post(url, data = body)
