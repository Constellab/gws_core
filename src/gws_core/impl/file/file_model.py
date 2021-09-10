# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from peewee import CharField

from ...extension.extended_resource_model import ExtendedResourceModel
from ...model.typing_register_decorator import typing_registrator
from .file_helper import FileHelper


@typing_registrator(unique_name="FileModel", object_type="MODEL", hide=True)
class FileModel(ExtendedResourceModel):
    path = CharField(null=True, index=True, unique=True)
    file_store_uri = CharField(null=True, index=True)
    _table_name = "gws_file_resource"

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        _json = super().to_json(deep=deep,  **kwargs)
        _json["filename"] = FileHelper.get_name_with_extension(self.path)
        _json["is_file"] = True
        return _json
