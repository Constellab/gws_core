from typing import List

from peewee import ForeignKeyField
from peewee import Model as PeeweeModel

from gws_core.folder.space_folder import SpaceFolder


class ModelWithFolder(PeeweeModel):
    folder: SpaceFolder = ForeignKeyField(SpaceFolder, null=True)

    @classmethod
    def clear_folder(cls, folders: List[SpaceFolder]) -> None:
        """
        Clear folders from all the entities that have the folder
        """

        cls.update(folder=None).where(cls.folder.in_(folders)).execute()
