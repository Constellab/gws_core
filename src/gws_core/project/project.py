# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from peewee import CharField, ForeignKeyField, ModelSelect

from ..core.model.model_with_user import ModelWithUser


class Project(ModelWithUser):
    """
    Project class.
    """
    code: str = CharField(null=False, max_length=20, default='')
    title: str = CharField(null=False, max_length=50)
    parent = ForeignKeyField('self', null=True, backref='children')

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
