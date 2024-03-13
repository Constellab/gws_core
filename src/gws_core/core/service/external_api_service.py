

import json
from typing import Any, Dict

import requests
from fastapi.encoders import jsonable_encoder
from requests.models import Response

from gws_core.core.exception.exceptions.base_http_exception import \
    BaseHTTPException

# 1 minute timeout
DEFAULT_TIMEOUT = 60


class ExternalApiService:
    """
    This class gives possibility to make http requests to external APIs
    """

    @classmethod
    def post(cls, url: str, body: Dict, headers: Dict[str, str] = None,
             raise_exception_if_error: bool = False, timeout: int = DEFAULT_TIMEOUT) -> Response:
        """
        Make an HTTP post request
        """
        if headers is None:
            headers = {}
        response = requests.post(url, json=jsonable_encoder(body), headers=headers, timeout=timeout)
        return cls._handle_response(response, raise_exception_if_error)

    @classmethod
    def put(cls, url: str, body: Dict, headers: Dict[str, str] = None, files: Any = None,
            raise_exception_if_error: bool = False, timeout: int = DEFAULT_TIMEOUT) -> Response:
        """
        Make an HTTP put request
        """
        if headers is None:
            headers = {}
        response = requests.put(url, json=jsonable_encoder(body), headers=headers, files=files, timeout=timeout)
        return cls._handle_response(response, raise_exception_if_error)

    @classmethod
    def put_form_data(cls, url: str, data: Any, headers: Dict[str, str] = None, files: Any = None,
                      raise_exception_if_error: bool = False, timeout: int = DEFAULT_TIMEOUT) -> Response:
        """
        Make an HTTP put request
        """
        if headers is None:
            headers = {}
        session = requests.Session()
        # Wrap the data in body key to retrive it
        # use the jsonable_encoder to convert the data to json
        # use the json.dumps to convert the data to string
        body = {"body": json.dumps(jsonable_encoder(data))}
        response = session.put(url, data=body, headers=headers, files=files, timeout=timeout)

        return cls._handle_response(response, raise_exception_if_error)

    @classmethod
    def get(cls, url: str, headers: Dict[str, str] = None, raise_exception_if_error: bool = False,
            timeout: int = DEFAULT_TIMEOUT) -> Response:
        """
        Make an HTTP get request
        """
        if headers is None:
            headers = {}
        response = requests.get(url, headers=headers, timeout=timeout)
        return cls._handle_response(response, raise_exception_if_error)

    @classmethod
    def delete(cls, url: str, headers: Dict[str, str] = None, raise_exception_if_error: bool = False,
               timeout: int = DEFAULT_TIMEOUT) -> Response:
        """
        Make an HTTP get request
        """
        if headers is None:
            headers = {}
        response = requests.delete(url, headers=headers, timeout=timeout)
        return cls._handle_response(response, raise_exception_if_error)

    @classmethod
    def _handle_response(cls, response: Response, raise_exception_if_error: bool) -> Response:
        """
        Handle the response of an HTTP request
        """
        if raise_exception_if_error and (response.status_code < 200 or response.status_code >= 300):
            cls.raise_error_from_response(response)
        return response

    @classmethod
    def raise_error_from_response(cls, response: Response) -> None:
        json_ = response.json()

        # if this is a constellab know error
        if 'status' in json_ and 'code' in json_ and 'detail' in json_ and \
                ('instanceId' in json_ or 'instance_id' in json_):
            raise BaseHTTPException(http_status_code=json_['status'],
                                    unique_code=json_['code'],
                                    detail=json_['detail'],
                                    instance_id=json_.get('instanceId') or json_.get('instance_id'))

        # otherwise raise the default exception
        raise BaseHTTPException(http_status_code=response.status_code, detail=response.text)
