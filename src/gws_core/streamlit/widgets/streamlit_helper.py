
import os
from typing import Any

from gws_core.core.utils.settings import Settings


class StreamlitHelper():

    CSS_PREFIX = 'st-key-'

    @classmethod
    def get_element_css_class(cls, key: str) -> str:
        return cls.CSS_PREFIX + key

    @classmethod
    def get_page_height(cls, additional_padding: int = 0) -> str:
        """Return the height of the page
        # 8*2px of main padding
        # 16px of main row wrap (of a column)

        :return: _description_
        :rtype: str
        """
        return f"calc(100vh - {32 + additional_padding}px)"

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
        with open(temp_file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        return temp_file_path
