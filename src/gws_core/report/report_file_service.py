# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import shutil
from typing import TypedDict

from fastapi import UploadFile
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.settings import Settings
from gws_core.core.utils.utils import Utils
from gws_core.impl.file.file_helper import FileHelper
from PIL import Image


class ReportImage(TypedDict):
    filename: str
    width: int
    height: int


class ReportFileService():
    """Service to store file (mainly image) linked to report

    :return: [description]
    :rtype: [type]
    """

    _dir_name = 'report'

    @classmethod
    def upload_file(cls, file: UploadFile) -> ReportImage:
        image = None
        try:
            image = Image.open(file.file)
            image_size = image.size
        except Exception:
            raise BadRequestException('The uploaded file is not an image')

        dir = cls._init_dir()

        # generate a file name
        extension = FileHelper.get_extension(file.filename)
        filename = Utils.generate_uuid() + '_' + str(DateHelper.now_utc_as_milliseconds()) + extension

        file_path = os.path.join(dir, filename)

        image.save(file_path)
        image.close()

        return {
            "filename": filename,
            'width': image_size[0],
            'height': image_size[1]
        }

    @classmethod
    def delete_file(cls, file_name: str) -> None:

        file_path = cls.get_file_path(file_name)
        FileHelper.delete_file(file_path)

    @classmethod
    def _init_dir(cls) -> str:
        dir = cls._get_dir_path()

        FileHelper.create_dir_if_not_exist(dir)
        return dir

    @classmethod
    def get_file_path(cls, filename: str) -> str:
        return os.path.join(cls._get_dir_path(), filename)

    @classmethod
    def _get_dir_path(cls) -> str:
        return os.path.join(Settings.retrieve().get_data_dir(), cls._dir_name)
