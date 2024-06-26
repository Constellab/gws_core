

import os

from fastapi import UploadFile
from PIL import Image

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.settings import Settings
from gws_core.core.utils.string_helper import StringHelper
from gws_core.impl.file.file_helper import FileHelper


class RichTextUploadImageResultDTO(BaseModelDTO):
    filename: str
    width: int
    height: int


class RichTextFileService():
    """Service to store file assosicated to a rich text (report, report template, RichTextParam)

    :return: [description]
    :rtype: [type]
    """

    _dir_name = 'report'

    @classmethod
    def upload_image(cls, file: UploadFile) -> RichTextUploadImageResultDTO:
        image: Image.Image = None
        try:
            image = Image.open(file.file)
        except Exception:
            raise BadRequestException('The uploaded file is not an image')

        # generate a file name
        # when the file data was set (like pasted from clipboard), the content type is 'application/octet-stream'
        if file.content_type == 'application/octet-stream':
            extension = 'png'
        else:
            extension = FileHelper.get_extension(file.filename)

        return cls.save_image(image, extension)

    @classmethod
    def save_image(cls, image: Image.Image, extension: str) -> RichTextUploadImageResultDTO:
        """
        Method to save the image of a report to the file system

        :param image: _description_
        :type image: Image.Image
        :param extension: _description_
        :type extension: str
        :return: _description_
        :rtype: RichTextUploadImageResultDTO
        """
        image_size = image.size

        filename = f"{StringHelper.generate_uuid()}_{str(DateHelper.now_utc_as_milliseconds())}.{extension}"

        dest_dir = cls._init_dir()
        file_path = os.path.join(dest_dir, filename)

        image.save(file_path)
        image.close()

        return RichTextUploadImageResultDTO(
            filename=filename,
            width=image_size[0],
            height=image_size[1]
        )

    @classmethod
    def delete_file(cls, file_name: str) -> None:

        file_path = cls.get_file_path(file_name)
        FileHelper.delete_file(file_path)

    @classmethod
    def _init_dir(cls) -> str:
        dir_ = cls._get_dir_path()

        FileHelper.create_dir_if_not_exist(dir_)
        return dir_

    @classmethod
    def get_file_path(cls, filename: str) -> str:
        return os.path.join(cls._get_dir_path(), filename)

    @classmethod
    def _get_dir_path(cls) -> str:
        return os.path.join(Settings.get_instance().get_data_dir(), cls._dir_name)
