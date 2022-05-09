# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from email.headerregistry import DateHeader
from time import time
from typing import Dict, Literal, TypedDict

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.utils.settings import ModuleInfo
from peewee import CharField

from ..core.model.model import Model
from ..model.typing_register_decorator import typing_registrator

BrickStatus = Literal['SUCCESS', 'ERROR', 'CRITICAL', 'WARNING']
BrickMessageStatus = Literal['INFO', 'ERROR', 'CRITICAL', 'WARNING']


class BrickMessage(TypedDict):
    message: str
    status: BrickMessageStatus
    timestamp: float


@typing_registrator(unique_name="BrickModel", object_type="MODEL", hide=True)
class BrickModel(Model):

    name: str = CharField(unique=True)
    status: BrickStatus = CharField()

    _table_name = "gws_brick"

    @classmethod
    def find_by_name(cls, name: str) -> 'BrickModel':
        try:
            return cls.get(cls.name == name)
        except:
            return None

    def add_message(self, message: str, status: BrickMessageStatus, timestamp: float = None) -> None:
        if 'messages' not in self.data:
            self.data['messages'] = []

        if timestamp is None:
            timestamp = time()

        brick_message: BrickMessage = {"message": message, "status": status, 'timestamp': timestamp}
        self.data['messages'].append(brick_message)

        # update the brick status
        if status == 'CRITICAL':
            self.status = 'CRITICAL'
        elif status == 'ERROR' and self.status != 'CRITICAL':
            self.status = 'ERROR'
        elif status == 'WARNING' and self.status == 'SUCCESS':
            self.status = 'WARNING'

    @property
    def messages(self) -> BrickMessage:
        return self.data['messages']

    def clear_messages(self) -> None:
        self.data['messages'] = []

    def get_brick_info(self) -> ModuleInfo:
        return BrickHelper.get_brick_info(self.name)

    @classmethod
    def delete_all(cls) -> None:
        cls.delete().execute(cls._db_manager.db)

    @classmethod
    def clear_all_message(cls) -> None:
        BrickModel.update(data={'messages': []}).execute(cls._db_manager.db)

    def to_json(self, deep: bool = False, **kwargs) -> Dict:
        json_ = super().to_json(deep=deep, **kwargs)

        try:
            brick_info = self.get_brick_info()
            json_['version'] = brick_info['version']
            json_['repo_type'] = brick_info['repo_type']
            json_['repo_commit'] = brick_info['repo_commit']
        except Exception as err:
            # If there was a problem during the birck loading, add a critical error and return brick
            self.add_message(str(err), 'CRITICAL')
            return super().to_json(deep=deep, **kwargs)
        return json_
