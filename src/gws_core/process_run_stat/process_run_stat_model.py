from typing import cast

from gws_core.core.model.model import Model
from gws_core.core.model.typed_db_field import (
    NullableCharField,
    NullableJSONField,
    TypedBooleanField,
    TypedCharField,
    TypedDateTimeUTC,
    TypedFloatField,
    TypedJSONField,
)
from gws_core.process_run_stat.process_run_stat_dto import (
    ProcessRunStatCreateDTO,
    ProcessRunStatDTO,
    ProcessRunStatLabEnv,
    ProcessRunStatStatus,
)


class ProcessRunStatModel(Model):
    process_typing_name: TypedCharField = TypedCharField()
    community_agent_version_id: NullableCharField = NullableCharField()
    status: TypedCharField = TypedCharField()
    error_info: NullableJSONField = NullableJSONField()
    started_at: TypedDateTimeUTC = TypedDateTimeUTC()
    ended_at: TypedDateTimeUTC = TypedDateTimeUTC()
    elapsed_time: TypedFloatField = TypedFloatField()
    brick_version_on_run: TypedCharField = TypedCharField()
    brick_version_on_create: TypedCharField = TypedCharField()
    config_value: TypedJSONField = TypedJSONField()
    lab_env: TypedCharField = TypedCharField()
    executed_by: TypedCharField = TypedCharField()
    sync_with_community: TypedBooleanField = TypedBooleanField()

    @classmethod
    def create_stat(cls, stat_data: ProcessRunStatCreateDTO) -> None:
        """Create and save a stat of a process run.

        :param stat_data: values of the run to save
        :type stat_data: ProcessRunStatCreateDTO
        """
        stat: ProcessRunStatModel = cls(**stat_data.model_dump(), sync_with_community=False)
        stat.save()

    def to_dto(self) -> ProcessRunStatDTO:
        return ProcessRunStatDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            process_typing_name=self.process_typing_name,
            community_agent_version_id=self.community_agent_version_id,
            status=cast(ProcessRunStatStatus, self.status),
            error_info=self.error_info,
            started_at=self.started_at,
            ended_at=self.ended_at,
            elapsed_time=self.elapsed_time,
            brick_version_on_run=self.brick_version_on_run,
            brick_version_on_create=self.brick_version_on_create,
            config_value=self.config_value,
            lab_env=cast(ProcessRunStatLabEnv, self.lab_env),
            executed_by=self.executed_by,
            sync_with_community=self.sync_with_community,
        )

    class Meta:
        table_name = "gws_process_run_stat"
        is_table = True
