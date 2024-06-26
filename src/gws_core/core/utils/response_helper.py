

import json
from io import StringIO
from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response, StreamingResponse

from gws_core.core.utils.xml_helper import XMLHelper


class ResponseHelper():

    @staticmethod
    def create_file_response_from_json(json_: dict, file_name: str = 'file.json',
                                       media_type: str = 'application/json') -> StreamingResponse:
        """
        Create a StreamingResponse from a json

        :param json: the json to stream
        :param file_name: the name of the file
        :param media_type: the media type of the file
        :return: the StreamingResponse
        """
        str_json = json.dumps(json_, indent=4)

        return ResponseHelper.create_file_response_from_str(str_json, file_name, media_type)

    @staticmethod
    def create_file_response_from_object(obj: Any, file_name: str = 'file.json',
                                         media_type: str = 'application/json') -> StreamingResponse:
        """
        Create a StreamingResponse from an object

        :param obj: the object to stream
        :param file_name: the name of the file
        :param media_type: the media type of the file
        :return: the StreamingResponse
        """
        str_json = jsonable_encoder(obj)

        return ResponseHelper.create_file_response_from_json(str_json, file_name, media_type)

    @staticmethod
    def create_file_response_from_str(text: str, file_name: str = 'file.txt',
                                      media_type: str = 'text/plain') -> StreamingResponse:
        """
        Create a StreamingResponse from a string

        :param text: the text to stream
        :param file_name: the name of the file
        :param media_type: the media type of the file
        :return: the StreamingResponse
        """
        # create a file-like object from the string
        file_like_object = StringIO(text)

        # create a StreamingResponse to stream the file
        response = StreamingResponse(iter([file_like_object.getvalue()]), media_type=media_type)

        # set the file name in the Content-Disposition header
        response.headers["Content-Disposition"] = f"attachment; filename={file_name}"

        return response

    @staticmethod
    def create_xml_response(xml_text: str, status_code: int = 200) -> Response:
        return Response(content=xml_text, media_type='application/xml',
                        status_code=status_code)

    @staticmethod
    def create_xml_response_from_json(json_: Any) -> Response:
        return ResponseHelper.create_xml_response(XMLHelper.dict_to_xml(json_))
