

from typing import Literal, TypedDict

from peewee import CharField

from ..core.model.model import Model
from ..model.typing_register_decorator import typing_registrator

BrickStatus = Literal['SUCCESS', 'ERROR', 'WARNING']
BrickMessageStatus = Literal['INFO', 'ERROR', 'WARNING']


class BrickMessage(TypedDict):
    message: str
    status: BrickMessageStatus
    timestamp: float


@typing_registrator(unique_name="BrickModel", object_type="MODEL", hide=True)
class BrickModel(Model):

    name: str = CharField(unique=True)
    path: str = CharField(unique=True)
    status: BrickStatus = CharField()

    _table_name = "gws_brick"

    @classmethod
    def find_by_name(cls, name: str) -> 'BrickModel':
        try:
            return cls.get(cls.name == name)
        except:
            return None

    def add_message(self, message: str, status: BrickMessageStatus, timestamp: float) -> None:
        if 'messages' not in self.data:
            self.data['messages'] = []

        brick_message: BrickMessage = {"message": message, "status": status, 'timestamp': timestamp}
        self.data['messages'].append(brick_message)

        # update the brick status
        if status == 'ERROR':
            self.status = 'ERROR'
        elif status == 'WARNING' and self.status == 'SUCCESS':
            self.status = 'WARNING'

    @property
    def messages(self) -> BrickMessage:
        return self.data['messages']

    def clear_messages(self) -> None:
        self.data['messages'] = []