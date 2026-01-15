import os
from typing import Any

from gws_core import Settings


class DocAssistantUtils:
    @classmethod
    def store_uploaded_file_in_tmp_dir(cls, uploaded_file: Any) -> str:
        """Store the uploaded file in a temporary directory

        :param uploaded_file: the uploaded file
        :type uploaded_file: UploadedFile
        :return: the path to the stored file
        :rtype: str
        """
        temp_dir = Settings.make_temp_dir()
        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return temp_file_path
