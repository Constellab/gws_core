import os
import re
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

    The object type is a plain ``str`` (not a :class:`RichTextObjectType`) so that other
    bricks can scope their own rich text files without extending the enum: gws_project
    stores the images of a project document under the ``project_document`` object type.
    :class:`RichTextObjectType` inherits ``str``, so its members can still be passed
    directly.

    :return: [description]
    :rtype: [type]
    """

    MAIN_DIR = "note"

    FILE_MAX_SIZE = 10 * 1024 * 1024  # 10 MB

    # The object type and id are used as directory names and reach this service straight from
    # a URL path (rich_text_controller), so they must not be able to escape the object dir.
    _PATH_SEGMENT_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

    # Names that must never be used as a file name: they are the only ones that can escape the
    # object dir. The character set is not restricted, because uploaded files keep their original
    # name (write_file), which may contain spaces or accents.
    _FORBIDDEN_FILENAMES = (os.curdir, os.pardir)

    ########################################### IMAGE ###########################################

    @classmethod
    def upload_image(
        cls, object_type: str, object_id: str, file: UploadFile
    ) -> RichTextUploadImageResultDTO:
        image: Image.Image | None = None
        try:
            image = Image.open(file.file)
        except Exception:
            raise BadRequestException("The uploaded file is not an image") from None

        # generate a file name
        # when the file data was set (like pasted from clipboard), the content type is 'application/octet-stream'
        extension: str
        if file.content_type == "application/octet-stream" or not file.filename:
            extension = "png"
        else:
            extension = FileHelper.get_normalized_extension(file.filename) or "png"

        return cls.save_image(object_type, object_id, image, extension)

    @classmethod
    def save_image(
        cls, object_type: str, object_id: str, image: Image.Image, extension: str
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
    def get_figure_file_path(cls, object_type: str, object_id: str, filename: str) -> str:
        return cls.get_object_file_path(object_type, object_id, filename)

    ########################################### FILE VIEW ###########################################

    @classmethod
    def get_file_view(cls, object_type: str, object_id: str, filename: str) -> CallViewResultDTO:
        file_path = cls.get_object_file_path(object_type, object_id, filename)

        with open(file_path, encoding="utf-8") as file:
            return CallViewResultDTO.from_json_str(file.read())

    @classmethod
    def save_file_view(
        cls, object_type: str, object_id: str, view_result: CallViewResultDTO
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
        cls, object_type: str, object_id: str, upload_file: UploadFile
    ) -> RichTextUploadFileResultDTO:
        if upload_file.size and upload_file.size > cls.FILE_MAX_SIZE:
            raise BadRequestException("The file is too large, the maximum size is 10 MB")

        if not upload_file.filename:
            raise BadRequestException("The file must have a name")

        return cls.write_file(
            object_type, object_id, upload_file.file.read(), upload_file.filename, "wb"
        )

    @classmethod
    def write_file(
        cls,
        object_type: str,
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
    def get_uploaded_file_path(cls, object_type: str, object_id: str, filename: str) -> str:
        return cls.get_object_file_path(object_type, object_id, filename)

    ########################################### GENERIC ###########################################

    @classmethod
    def get_object_file_path(cls, object_type: str, object_id: str, filename: str) -> str:
        """Return the path of a file of an object, checking that it stays inside the object dir.

        :param object_type: Type of the object owning the file
        :type object_type: str
        :param object_id: Id of the object owning the file
        :type object_id: str
        :param filename: Name of the file, without any directory component
        :type filename: str
        :raises BadRequestException: If the object type, id or filename is invalid, or if the
            resulting path escapes the object directory.
        :return: The absolute path of the file
        :rtype: str
        """
        object_dir = cls.get_object_dir_path(object_type, object_id)

        cls._check_filename(filename)

        file_path = os.path.normpath(os.path.join(object_dir, filename))

        # Defense in depth: the filename pattern already rejects any directory component, but the
        # served files are readable without authentication, so the resolved path is checked too.
        if os.path.commonpath([os.path.normpath(object_dir), file_path]) != os.path.normpath(
            object_dir
        ):
            raise BadRequestException(f"Invalid file name '{filename}'")

        return file_path

    @classmethod
    def get_object_dir_path(cls, object_type: str, object_id: str) -> str:
        """Return the directory storing the files of an object.

        :param object_type: Type of the object owning the files. A
            :class:`RichTextObjectType` member or any brick specific value
            (e.g. ``project_document``).
        :type object_type: str
        :param object_id: Id of the object owning the files
        :type object_id: str
        :raises BadRequestException: If the object type is the note resource one (it does not
            use this service), or if the type or id is not a valid directory name.
        :return: The absolute path of the object directory
        :rtype: str
        """
        if object_type == RichTextObjectType.NOTE_RESOURCE.value:
            raise BadRequestException("The object type note resource does ont use the file service")

        cls._check_path_segment(object_type, "object type")
        cls._check_path_segment(object_id, "object id")

        return os.path.join(cls._get_dir_path(), object_type, object_id)

    @classmethod
    def _check_path_segment(cls, value: str, name: str) -> None:
        """Check that a value can safely be used as a directory name.

        The object type and id are concatenated into a filesystem path and come straight from
        the request URL, so they must be rejected if they could escape the object directory.
        """
        if not value or not cls._PATH_SEGMENT_PATTERN.match(value):
            raise BadRequestException(f"Invalid {name} '{value}'")

    @classmethod
    def _check_filename(cls, filename: str) -> None:
        """Check that a value can safely be used as a file name inside the object directory.

        The filename comes straight from the request URL and the image route is public, so it
        must not be able to point at a file outside of the object directory: it must be a bare
        name, without any directory component (``..``, an absolute path or a nested path).

        The character set is intentionally not restricted: files uploaded through
        :meth:`write_file` keep their original name, which may contain spaces or accents.
        """
        if not filename or filename in cls._FORBIDDEN_FILENAMES:
            raise BadRequestException(f"Invalid file name '{filename}'")

        # A bare name is its own basename on both posix and windows separators, and is relative.
        if (
            os.path.isabs(filename)
            or os.path.basename(filename) != filename
            or "/" in filename
            or "\\" in filename
        ):
            raise BadRequestException(f"Invalid file name '{filename}'")

    @classmethod
    def create_object_dir(cls, object_type: str, object_id: str) -> None:
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
    def delete_object_dir(cls, object_type: str, object_id: str) -> None:
        FileHelper.delete_dir(cls.get_object_dir_path(object_type, object_id))

    @classmethod
    def copy_object_dir(
        cls,
        source_object_type: str,
        source_object_id: str,
        target_object_type: str,
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
