
from peewee import Model as PeeweeModel

from gws_core.core.model.typed_db_field import NullableForeignKeyField
from gws_core.folder.space_folder import SpaceFolder


class ModelWithFolder(PeeweeModel):
    folder = NullableForeignKeyField(SpaceFolder)

    @classmethod
    def clear_folder(cls, folders: list[SpaceFolder]) -> None:
        """
        Clear folders from all the entities that have the folder
        """

        cls.update(folder=None).where(cls.folder.in_(folders)).execute()
