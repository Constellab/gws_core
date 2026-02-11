import json
import mimetypes
import os
from io import StringIO
from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response, StreamingResponse

from gws_core.core.utils.xml_helper import XMLHelper


class ResponseHelper:
    @staticmethod
    def create_file_response_from_json(
        json_: dict, file_name: str = "file.json", media_type: str = "application/json"
    ) -> StreamingResponse:
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
    def create_file_response_from_object(
        obj: Any, file_name: str = "file.json", media_type: str = "application/json"
    ) -> StreamingResponse:
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
    def create_file_response_from_str(
        text: str, file_name: str = "file.txt", media_type: str = "text/plain"
    ) -> StreamingResponse:
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
    def create_file_response_from_path(
        file_path: str, file_name: str | None = None, media_type: str | None = None
    ) -> StreamingResponse:
        """
        Create a StreamingResponse from a file path on the local filesystem.

        :param file_path: the path to the file on disk
        :param file_name: the name of the file in the response. If None, uses the basename of file_path
        :param media_type: the media type of the file. If None, it is guessed from the file extension
        :return: the StreamingResponse
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_name is None:
            file_name = os.path.basename(file_path)

        if media_type is None:
            guessed_type, _ = mimetypes.guess_type(file_path)
            media_type = guessed_type or "application/octet-stream"

        def iter_file():
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    yield chunk

        response = StreamingResponse(iter_file(), media_type=media_type)
        response.headers["Content-Disposition"] = f"attachment; filename={file_name}"

        return response

    @staticmethod
    def create_xml_response(xml_text: str, status_code: int = 200) -> Response:
        return Response(content=xml_text, media_type="application/xml", status_code=status_code)

    @staticmethod
    def create_xml_response_from_json(json_: Any) -> Response:
        return ResponseHelper.create_xml_response(XMLHelper.dict_to_xml(json_))
        # return ResponseHelper.create_xml_response(
        #     '<?xml version="1.0" encoding="utf-8"?>\n<Tagging><VersionId>null</VersionId><TagSet><Key>key</Key><Value>c4daa057-1b06-4b05-9409-bb0ed7a012bf_1726063810413.csv</Value></TagSet></Tagging>')


#         return ResponseHelper.create_xml_response("""
# <Tagging xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
#     <TagSet>
#         <Tag>
#             <Key>tag1</Key>
#             <Value>val1</Value>
#         </Tag>
#         <Tag>
#             <Key>tag2</Key>
#             <Value>val2</Value>
#         </Tag>
#     </TagSet>
# </Tagging>"""
#   )
