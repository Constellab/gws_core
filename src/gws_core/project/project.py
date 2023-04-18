# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from peewee import CharField, ForeignKeyField, ModelSelect

from gws_core.core.model.model import Model


class Project(Model):
    """
    Project class.
    """
    code: str = CharField(null=False, max_length=20, default='')
    title: str = CharField(null=False, max_length=50)
    parent = ForeignKeyField('self', null=True, backref='children', on_delete='CASCADE')

    children: List['Project']

    _table_name = 'gws_project'

    def archive(self, archive: bool) -> 'Project':
        """
        Deactivated method.
        """

        return None

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        children = [child.to_json(deep=deep) for child in self.children] if deep else []

        json_ = super().to_json(deep, **kwargs)
        json_['children'] = children

        return json_

    @classmethod
    def get_roots(cls) -> ModelSelect:
        """
        Get all root projects.
        """

        return cls.select().where(cls.parent.is_null())

    def get_hierarchy_as_list(self) -> List['Project']:
        """
        Get all projects and children as a list.
        """

        children = [self]
        for child in self.children:
            children += child.get_hierarchy_as_list()

        return children

    def _before_insert(self) -> None:
        pass

    def _before_update(self) -> None:
        pass
