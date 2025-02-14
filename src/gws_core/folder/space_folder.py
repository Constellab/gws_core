

from typing import List

from peewee import CharField, ForeignKeyField, ModelSelect

from gws_core.core.model.model import Model
from gws_core.folder.space_folder_dto import SpaceFolderDTO, SpaceFolderTreeDTO


class SpaceFolder(Model):
    name: str = CharField(null=False, max_length=100)
    parent: 'SpaceFolder' = ForeignKeyField('self', null=True, backref='children', on_delete='CASCADE')

    children: List['SpaceFolder']

    _table_name = 'gws_folder'

    def to_dto(self) -> SpaceFolderDTO:
        return SpaceFolderDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            name=self.name,
        )

    def to_tree_dto(self) -> SpaceFolderTreeDTO:
        children = [child.to_tree_dto() for child in self.children]

        # sort children by title
        children.sort(key=lambda x: x.name)

        return SpaceFolderTreeDTO(
            **self.to_dto().to_json_dict(),
            children=children
        )

    def get_root(self) -> 'SpaceFolder':
        """
        Get the root folder of the current folder.
        """

        if self.parent is None:
            return self
        else:
            return self.parent.get_root()

    @classmethod
    def get_roots(cls) -> ModelSelect:
        """
        Get all root folders.
        """

        return cls.select().where(cls.parent.is_null()).order_by(cls.name)

    def get_with_children_as_list(self) -> List['SpaceFolder']:
        """
        Get current folder and children as a list.
        """

        children = [self]
        for child in self.children:
            children += child.get_with_children_as_list()

        return children

    def has_ancestor(self, id_: str) -> bool:
        """
        Check if the folder has an ancestor with the given id.
        """

        if self.parent is None:
            return False

        if self.parent.id == id_:
            return True

        return self.parent.has_ancestor(id_)

    def _before_insert(self) -> None:
        pass

    def _before_update(self) -> None:
        pass
