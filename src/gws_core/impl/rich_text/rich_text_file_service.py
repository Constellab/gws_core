import os
from enum import Enum
from typing import Any

from fastapi import UploadFile
from PIL import Image

from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.settings import Settings
from gws_core.core.utils.string_helper import StringHelper
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.rich_text.rich_text_types import RichTextObjectType
from gws_core.resource.view.view_dto import CallViewResultDTO


class RichTextUploadImageResultDTO(BaseModelDTO):
    filename: str
    width: int
    height: int


class RichTextUploadFileResultDTO(BaseModelDTO):
    name: str
    size: int  # in bytes


class RichTextFileService:
    """Service to store file assosicated to a rich text (note, note template)

    Files are stored in the 'note' directory in the data directory
    For each object (note, note template), a directory (from id) is created to store the files

    Path example : data_dir/note/note/{note_id}/filename

    :return: [description]
    :rtype: [type]
    """

    MAIN_DIR = "note"

    FILE_MAX_SIZE = 10 * 1024 * 1024  # 10 MB

    ########################################### IMAGE ###########################################

    @classmethod
    def upload_image(
        cls, object_type: RichTextObjectType, object_id: str, file: UploadFile
    ) -> RichTextUploadImageResultDTO:
        image: Image.Image = None
        try:
            image = Image.open(file.file)
        except Exception:
            raise BadRequestException("The uploaded file is not an image")

        # generate a file name
        # when the file data was set (like pasted from clipboard), the content type is 'application/octet-stream'
        if file.content_type == "application/octet-stream":
            extension = "png"
        else:
            extension = FileHelper.get_extension(file.filename)

        return cls.save_image(object_type, object_id, image, extension)

    @classmethod
    def save_image(
        cls, object_type: RichTextObjectType, object_id: str, image: Image.Image, extension: str
    ) -> RichTextUploadImageResultDTO:
        """
        Method to save the image of a note to the file system

        :param image: _description_
        :type image: Image.Image
        :param extension: _description_
        :type extension: str
        :return: _description_
        :rtype: RichTextUploadImageResultDTO
        """
        image_size = image.size

        filename = cls._generate_filename(extension)

        cls.create_object_dir(object_type, object_id)
        file_path = cls.get_object_file_path(object_type, object_id, filename)

        image.save(file_path)
        image.close()

        return RichTextUploadImageResultDTO(
            filename=filename, width=image_size[0], height=image_size[1]
        )

    @classmethod
    def get_figure_file_path(
        cls, object_type: RichTextObjectType, object_id: str, filename: str
    ) -> str:
        return cls.get_object_file_path(object_type, object_id, filename)

    ########################################### FILE VIEW ###########################################

    @classmethod
    def get_file_view(
        cls, object_type: RichTextObjectType, object_id: str, filename: str
    ) -> CallViewResultDTO:
        file_path = cls.get_object_file_path(object_type, object_id, filename)

        with open(file_path, "r", encoding="utf-8") as file:
            return CallViewResultDTO.from_json_str(file.read())

    @classmethod
    def save_file_view(
        cls, object_type: RichTextObjectType, object_id: str, view_result: CallViewResultDTO
    ) -> str:
        cls.create_object_dir(object_type, object_id)
        filename = cls._generate_filename("json")

        file_path = cls.get_object_file_path(object_type, object_id, filename)

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(view_result.to_json_str())

        return filename

    ########################################### FILE ###########################################

    @classmethod
    def upload_file(
        cls, object_type: RichTextObjectType, object_id: str, upload_file: UploadFile
    ) -> RichTextUploadFileResultDTO:
        if upload_file.size > cls.FILE_MAX_SIZE:
            raise BadRequestException("The file is too large, the maximum size is 10 MB")

        return cls.write_file(
            object_type, object_id, upload_file.file.read(), upload_file.filename, "wb"
        )

    @classmethod
    def write_file(
        cls,
        object_type: RichTextObjectType,
        object_id: str,
        file_content: Any,
        filename: str,
        mode: str,
    ) -> RichTextUploadFileResultDTO:
        cls.create_object_dir(object_type, object_id)

        # generate a unique name for the file for the object
        filename = FileHelper.generate_unique_fs_node_for_dir(
            filename, cls.get_object_dir_path(object_type, object_id)
        )

        # write the file
        file_path = cls.get_object_file_path(object_type, object_id, filename)

        encoding = "utf-8" if mode == "w" else None
        with open(file_path, mode, encoding=encoding) as file:
            file.write(file_content)

        return RichTextUploadFileResultDTO(name=filename, size=FileHelper.get_size(file_path))

    @classmethod
    def get_uploaded_file_path(
        cls, object_type: RichTextObjectType, object_id: str, filename: str
    ) -> str:
        return cls.get_object_file_path(object_type, object_id, filename)

    ########################################### GENERIC ###########################################

    @classmethod
    def get_object_file_path(
        cls, object_type: RichTextObjectType, object_id: str, filename: str
    ) -> str:
        return os.path.join(cls.get_object_dir_path(object_type, object_id), filename)

    @classmethod
    def get_object_dir_path(cls, object_type: RichTextObjectType, object_id: str) -> str:
        if object_type == RichTextObjectType.NOTE_RESOURCE:
            raise BadRequestException("The object type note resource does ont use the file service")

        return os.path.join(cls._get_dir_path(), object_type.value, object_id)

    @classmethod
    def create_object_dir(cls, object_type: RichTextObjectType, object_id: str) -> None:
        FileHelper.create_dir_if_not_exist(cls.get_object_dir_path(object_type, object_id))

    @classmethod
    def _generate_filename(cls, extension: str) -> str:
        return f"{StringHelper.generate_uuid()}_{str(DateHelper.now_utc_as_milliseconds())}.{extension}"

    @classmethod
    def _get_dir_path(cls) -> str:
        dir_ = os.path.join(Settings.get_instance().get_data_dir(), cls.MAIN_DIR)

        FileHelper.create_dir_if_not_exist(dir_)
        return dir_

    @classmethod
    def delete_object_dir(cls, object_type: RichTextObjectType, object_id: str) -> None:
        FileHelper.delete_dir(cls.get_object_dir_path(object_type, object_id))

    @classmethod
    def copy_object_dir(
        cls,
        source_object_type: RichTextObjectType,
        source_object_id: str,
        target_object_type: RichTextObjectType,
        target_object_id: str,
    ) -> None:
        source_dir = cls.get_object_dir_path(source_object_type, source_object_id)
        target_dir = cls.get_object_dir_path(target_object_type, target_object_id)

        if not FileHelper.exists_on_os(source_dir):
            return

        if FileHelper.exists_on_os(target_dir):
            FileHelper.copy_dir_content_to_dir(source_dir, target_dir)
        else:
            FileHelper.copy_dir(source_dir, target_dir)
