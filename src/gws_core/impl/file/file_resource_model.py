# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

from peewee import CharField

from ...model.typing_manager import TypingManager
from ...model.typing_register_decorator import typing_registrator
from ...resource.resource import SerializedResourceData
from ...resource.resource_model import ResourceModel
from .file_helper import FileHelper
from ...extension.extended_resource_model import ExtendedResourceModel

@typing_registrator(unique_name="FileResourceModel", object_type="GWS_CORE", hide=True)
class FileResourceModel(ExtendedResourceModel):
    path = CharField(null=True, index=True, unique=True)
    file_store_uri = CharField(null=True, index=True)
    _table_name = "gws_file_resource"

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        _json = super().to_json(deep=deep,  **kwargs)
        _json["filename"] = FileHelper.get_name_with_extension(self.path)
        _json["is_file"] = True
        return _json
