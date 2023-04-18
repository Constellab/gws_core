# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import hashlib
from json import dumps
from typing import List, Optional

from peewee import CharField, IntegerField
from typing_extensions import TypedDict

from gws_core.brick.brick_dto import BrickVersion
from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.model.base_model import BaseModel
from gws_core.core.utils.string_helper import StringHelper

from ..core.model.db_field import DateTimeUTC, JSONField
from ..core.utils.date_helper import DateHelper

LAB_CONFIG_VERSION = 1


class LabConfig(TypedDict):
    """Object representing the complete config of a lab to recreate it
    """
    version: int  # version of the config
    brick_versions: List[BrickVersion]


class LabConfigModel(BaseModel):
    """Class to store the configurations of the lab

    :param BaseModel: _description_
    :type BaseModel: _type_
    """

    id = CharField(primary_key=True, max_length=36)
    created_at = DateTimeUTC(default=DateHelper.now_utc)
    version = IntegerField(null=False)  # version of the config
    brick_versions: List[BrickVersion] = JSONField(null=False)
    hash = CharField(null=False)

    _table_name = 'gws_lab_config'

    _current_config: 'LabConfigModel' = None

    @classmethod
    def save_current_config(cls) -> 'LabConfigModel':
        """Save the current config of the lab

        :return: _description_
        :rtype: LabConfigModel
        """
        brick_versions = BrickHelper.get_all_brick_versions()

        cls._current_config = cls.create_config_if_not_exits(brick_versions)
        return cls._current_config

    @classmethod
    def get_current_config(cls) -> 'LabConfigModel':
        if cls._current_config is None:
            cls.save_current_config()
        return cls._current_config

    @classmethod
    def create_config_if_not_exits(cls, brick_versions: List[BrickVersion]) -> 'LabConfigModel':
        hash = cls._hash_versions(brick_versions)
        lab_config = cls._find_by_hash(hash)

        if lab_config is not None:
            return lab_config

        return cls._create(hash, brick_versions)

    @classmethod
    def _create(cls, hash: str, brick_versions: List[BrickVersion]) -> 'LabConfigModel':
        lab_config = LabConfigModel()
        lab_config.id = StringHelper.generate_uuid()
        lab_config.hash = hash
        lab_config.brick_versions = brick_versions
        lab_config.version = LAB_CONFIG_VERSION

        return lab_config.save(force_insert=True)

    @classmethod
    def _find_by_hash(cls, hash: str) -> Optional['LabConfigModel']:
        return cls.select().where((cls.hash == hash) & (cls.version == LAB_CONFIG_VERSION)).first()

    @classmethod
    def _hash_versions(cls, brick_versions: List[BrickVersion]) -> str:
        # sort brick by name before hasing
        brick_versions = sorted(brick_versions, key=lambda d: d['name'])
        hash_obj = hashlib.blake2b()
        hash_obj.update(dumps(brick_versions).encode())

        return hash_obj.hexdigest()

    def to_json(self) -> LabConfig:
        return {
            'version': self.version,
            'brick_versions': self.brick_versions
        }
