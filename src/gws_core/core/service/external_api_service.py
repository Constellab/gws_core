

import json
import tempfile
from io import BufferedReader
from typing import Any, Dict, List, Tuple

import requests
from fastapi.encoders import jsonable_encoder
from requests.models import Response

from gws_core.core.exception.exceptions.base_http_exception import \
    BaseHTTPException
from gws_core.impl.file.file_helper import FileHelper

# 1 minute timeout
DEFAULT_TIMEOUT = 60


class FormData():

    file_paths: List[Tuple[str, str, str]]
    json_data: List[Tuple[str, Any]]

    _opened_files: List[BufferedReader]

    def __init__(self):
        self.file_paths = []
        self.json_data = []
        self._opened_files = []

    def add_file_from_path(self, key: str,  file_path: str, filename: str = None) -> None:
        self.file_paths.append((key, file_path, filename))

    def add_file_from_json(self, json_data: Any, key: str, filename: str) -> None:
        """
        Create a file from the json and add it to the form data.
        """
        # Create temporary file for the file view
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(json_data, tmp_file)
            self.add_file_from_path(key, tmp_file.name, filename)

    def add_json_data(self, key: str, data: Any) -> None:
        self.json_data.append((key, data))

    def __enter__(self) -> List:
        data: List = []
        for key, file_path, filename in self.file_paths:
            file_name = filename if filename else FileHelper.get_name_with_extension(file_path)
            content_type = FileHelper.get_mime(file_path)
            opened_file = open(file_path, 'rb')
            data.append((key, (file_name, opened_file, content_type)))
            self._opened_files.append(opened_file)

        for key, obj in self.json_data:
            obj_str = json.dumps(jsonable_encoder(obj))
            data.append((key, (None, obj_str, 'text/plain')))

        return data

    def __exit__(self, exc_type, exc_val, exc_tb):
        for file in self._opened_files:
            file.close()
        # raise the exception if exists
        if exc_val:
            raise exc_val
        return False


class ExternalApiService:
    """
    This class gives possibility to make http requests to external APIs
    """

    @classmethod
    def post(cls, url: str, body: Any, headers: Dict[str, str] = None,
             raise_exception_if_error: bool = False, timeout: int = DEFAULT_TIMEOUT) -> Response:
        """
        Make an HTTP post request
        """
        if headers is None:
            headers = {}
        response = requests.post(url, json=jsonable_encoder(body), headers=headers, timeout=timeout)
        return cls._handle_response(response, raise_exception_if_error)

    @classmethod
    def post_form_data(cls, url: str, form_data: FormData,
                       data: Any = None, headers: Dict[str, str] = None,
                       raise_exception_if_error: bool = False,
                       timeout: int = DEFAULT_TIMEOUT) -> Response:
        """
        Make an HTTP post request
        """
        if headers is None:
            headers = {}
        session = requests.Session()
        with form_data as files:
            response = session.post(url, data=data, headers=headers, files=files, timeout=timeout)

        return cls._handle_response(response, raise_exception_if_error)

    @classmethod
    def put(cls, url: str, body: Any, headers: Dict[str, str] = None, files: Any = None,
            raise_exception_if_error: bool = False, timeout: int = DEFAULT_TIMEOUT) -> Response:
        """
        Make an HTTP put request
        """
        if headers is None:
            headers = {}
        response = requests.put(url, json=jsonable_encoder(body), headers=headers, files=files, timeout=timeout)
        return cls._handle_response(response, raise_exception_if_error)

    @classmethod
    def put_form_data(cls, url: str, form_data: FormData, data: Any = None, headers: Dict[str, str] = None,
                      raise_exception_if_error: bool = False, timeout: int = DEFAULT_TIMEOUT) -> Response:
        """
        Make an HTTP put request
        """
        if headers is None:
            headers = {}

        with form_data as files:
            session = requests.Session()
            response = session.put(url, data=data, headers=headers, files=files, timeout=timeout)

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

        json_: dict = None
        try:
            json_ = response.json()
        except Exception:
            # otherwise raise the default exception
            raise BaseHTTPException(http_status_code=response.status_code, detail=response.text)

        # if this is a constellab know error
        if 'status' in json_ and 'code' in json_ and 'detail' in json_ and \
                ('instanceId' in json_ or 'instance_id' in json_):
            raise BaseHTTPException(http_status_code=json_['status'],
                                    unique_code=json_['code'],
                                    detail=json_['detail'],
                                    instance_id=json_.get('instanceId') or json_.get('instance_id'))

        # otherwise raise the default exception
        raise BaseHTTPException(http_status_code=response.status_code, detail=response.text)
