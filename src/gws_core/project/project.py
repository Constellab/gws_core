

from typing import List

from peewee import CharField, ForeignKeyField, ModelSelect

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.model.model import Model
from gws_core.project.project_dto import (ProjectDTO, ProjectLevelStatus,
                                          ProjectTreeDTO)


class Project(Model):
    """
    Project class.
    """
    code: str = CharField(null=False, max_length=20, default='')
    title: str = CharField(null=False, max_length=100)
    parent = ForeignKeyField('self', null=True, backref='children', on_delete='CASCADE')
    level_status = EnumField(choices=ProjectLevelStatus, max_length=20)

    children: List['Project']

    _table_name = 'gws_project'

    def to_dto(self) -> ProjectDTO:
        return ProjectDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            code=self.code,
            title=self.title,
            levelStatus=self.level_status
        )

    def to_tree_dto(self) -> ProjectTreeDTO:
        children = [child.to_tree_dto() for child in self.children]

        return ProjectTreeDTO(
            **self.to_dto().to_json_dict(),
            children=children
        )

    @classmethod
    def get_roots(cls) -> ModelSelect:
        """
        Get all root projects.
        """

        return cls.select().where(cls.parent.is_null())

    def get_with_children_as_list(self) -> List['Project']:
        """
        Get current project and children as a list.
        """

        children = [self]
        for child in self.children:
            children += child.get_with_children_as_list()

        return children

    def _before_insert(self) -> None:
        pass

    def _before_update(self) -> None:
        pass
