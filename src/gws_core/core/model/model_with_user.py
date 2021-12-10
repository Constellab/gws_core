

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
    created_by = ForeignKeyField(User, null=False, backref='+')
    last_modified_by = ForeignKeyField(User, null=False, backref='+')

    def _before_insert(self) -> None:
        super()._before_insert()
        self.created_by = CurrentUserService.get_and_check_current_user()
        self.last_modified_by = CurrentUserService.get_and_check_current_user()

    def _before_update(self) -> None:
        super()._before_update()
        self.last_modified_by = CurrentUserService.get_and_check_current_user()

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        json_ = super().to_json(deep=deep, **kwargs)

        # add the created by and last_modeified_by
        json_["created_by"] = self.created_by.to_json()
        json_["last_modified_by"] = self.last_modified_by.to_json()
        return json_
