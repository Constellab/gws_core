# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from io import StringIO

from fastapi.responses import StreamingResponse


class ResponseHelper():

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
