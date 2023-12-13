# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from time import time
from typing import Any, Dict, List

from peewee import CharField

from gws_core.brick.brick_dto import (BrickDTO, BrickInfo, BrickMessageDTO,
                                      BrickMessageStatus, BrickStatus)
from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.model.db_field import JSONField

from ..core.model.model import Model


class BrickModel(Model):

    name: str = CharField(unique=True)
    status: BrickStatus = CharField()
    data: Dict[str, Any] = JSONField(null=True)

    _table_name = "gws_brick"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_saved() and not self.data:
            self.data = {}

    def add_message(self, message: str, status: BrickMessageStatus, timestamp: float = None) -> None:
        if 'messages' not in self.data:
            self.data['messages'] = []

        if timestamp is None:
            timestamp = time()

        brick_message = {
            "message": message, "status": status, 'timestamp': timestamp}
        self.data['messages'].append(brick_message)

        # update the brick status
        if status == 'CRITICAL':
            self.status = 'CRITICAL'
        elif status == 'ERROR' and self.status != 'CRITICAL':
            self.status = 'ERROR'
        elif status == 'WARNING' and self.status == 'SUCCESS':
            self.status = 'WARNING'

    def get_messages(self) -> List[BrickMessageDTO]:
        return BrickMessageDTO.from_json_list(self.data['messages'])

    def clear_messages(self) -> None:
        self.data['messages'] = []

    def get_brick_info(self) -> BrickInfo:
        return BrickHelper.get_brick_info_and_check(self.name)

    def to_dto(self) -> BrickDTO:
        brick_dto = BrickDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            name=self.name,
            status=self.status,
            messages=self.get_messages()
        )

        try:
            brick_info = self.get_brick_info()
            brick_dto.version = brick_info['version']
            brick_dto.repo_type = brick_info['repo_type']
            brick_dto.brick_path = brick_info['path']
            brick_dto.repo_commit = brick_info['repo_commit']
            brick_dto.parent_name = brick_info['parent_name']

        except Exception as err:
            brick_dto.messages.append(
                BrickMessageDTO(
                    message=f"Can't find brick '{self.name}', was it removed from the lab ? Error : {str(err)}",
                    status='CRITICAL',
                    timestamp=time()
                )
            )

        return brick_dto

    ################################################## CLASS METHODS ##################################################

    @classmethod
    def find_by_name(cls, name: str) -> 'BrickModel':
        try:
            return cls.get(cls.name == name)
        except:
            return None

    @classmethod
    def delete_all(cls) -> None:
        cls.delete().execute(cls._db_manager.db)

    @classmethod
    def clear_all_message(cls) -> None:
        BrickModel.update(data={'messages': []}).execute(cls._db_manager.db)

    class Meta:
        table_name = 'gws_brick'
