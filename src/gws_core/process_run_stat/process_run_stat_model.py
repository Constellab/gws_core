from datetime import datetime
from typing import Dict

from peewee import BooleanField, CharField, FloatField

from gws_core.core.model.db_field import DateTimeUTC, JSONField
from gws_core.core.model.model import Model
from gws_core.process_run_stat.process_run_stat_dto import (
    ProcessRunStatDTO, ProcessRunStatLabEnv, ProcessRunStatStatus)


class ProcessRunStatModel(Model):

    _table_name = 'gws_process_run_stat'

    process_typing_name: str = CharField()
    community_agent_version_id: str = CharField(null=True)
    status: ProcessRunStatStatus = CharField()
    error_info: Dict = JSONField(null=True)
    started_at: datetime = DateTimeUTC()
    ended_at: datetime = DateTimeUTC()
    elapsed_time: float = FloatField()
    brick_version_on_run: str = CharField()
    brick_version_on_create: str = CharField()
    config_value: Dict = JSONField()
    lab_env: ProcessRunStatLabEnv = CharField()
    executed_by: str = CharField()
    sync_with_community: bool = BooleanField()

    def to_dto(self) -> ProcessRunStatDTO:
        return ProcessRunStatDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            process_typing_name=self.process_typing_name,
            community_agent_version_id=self.community_agent_version_id,
            status=self.status,
            error_info=self.error_info,
            started_at=self.started_at,
            ended_at=self.ended_at,
            elapsed_time=self.elapsed_time,
            brick_version_on_run=self.brick_version_on_run,
            brick_version_on_create=self.brick_version_on_create,
            config_value=self.config_value,
            lab_env=self.lab_env,
            executed_by=self.executed_by,
            sync_with_community=self.sync_with_community
        )
