# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from peewee import ForeignKeyField

from ...user.current_user_service import CurrentUserService
from ...user.user import User
from .model import Model


class ModelWithUser(Model):
    """Model class with created_by and last_modified_by columns automatically provided

    :param Model: [description]
    :type Model: [type]
    :return: [description]
    :rtype: [type]
    """
    # set null=True because otherwise the attribute can't be None, peewee prevents it
    created_by = ForeignKeyField(User, null=True, backref='+')
    last_modified_by = ForeignKeyField(User, null=True, backref='+')

    def _before_insert(self) -> None:
        super()._before_insert()
        self.created_by = CurrentUserService.get_and_check_current_user()
        self.last_modified_by = CurrentUserService.get_and_check_current_user()

    def _before_update(self) -> None:
        super()._before_update()
        self.last_modified_by = CurrentUserService.get_and_check_current_user()

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        json_ = super().to_json(deep=deep, **kwargs)

        # add the created by and last_modified_by
        if self.created_by:
            json_["created_by"] = self.created_by.to_json()

        if self.last_modified_by:
            json_["last_modified_by"] = self.last_modified_by.to_json()
        return json_
