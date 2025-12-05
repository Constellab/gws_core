from datetime import datetime

from gws_core.core.model.db_field import DateTimeUTC, JSONField
from gws_core.core.model.model import Model
from gws_core.process_run_stat.process_run_stat_dto import (
    ProcessRunStatDTO,
    ProcessRunStatLabEnv,
    ProcessRunStatStatus,
)
from peewee import BooleanField, CharField, FloatField


class ProcessRunStatModel(Model):
    process_typing_name: str = CharField()
    community_agent_version_id: str = CharField(null=True)
    status: ProcessRunStatStatus = CharField()
    error_info: dict = JSONField(null=True)
    started_at: datetime = DateTimeUTC()
    ended_at: datetime = DateTimeUTC()
    elapsed_time: float = FloatField()
    brick_version_on_run: str = CharField()
    brick_version_on_create: str = CharField()
    config_value: dict = JSONField()
    lab_env: ProcessRunStatLabEnv = CharField()
    executed_by: str = CharField()
    sync_with_community: bool = BooleanField()

    @classmethod
    def create_stat(
        cls,
        process_typing_name: str,
        status: ProcessRunStatStatus,
        started_at: datetime,
        ended_at: datetime,
        elapsed_time: float,
        brick_version_on_run: str,
        brick_version_on_create: str,
        config_value: dict,
        lab_env: ProcessRunStatLabEnv,
        executed_by: str,
        error_info: dict | None = None,
        community_agent_version_id: str | None = None,
    ) -> None:
        stat: ProcessRunStatModel = ProcessRunStatModel()
        stat.process_typing_name = process_typing_name
        stat.community_agent_version_id = community_agent_version_id
        stat.status = status
        stat.error_info = error_info
        stat.started_at = started_at
        stat.ended_at = ended_at
        stat.elapsed_time = elapsed_time
        stat.brick_version_on_run = brick_version_on_run
        stat.brick_version_on_create = brick_version_on_create
        stat.config_value = config_value
        stat.lab_env = lab_env
        stat.executed_by = executed_by

        stat.save()

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
            sync_with_community=self.sync_with_community,
        )

    class Meta:
        table_name = "gws_process_run_stat"
        is_table = True
