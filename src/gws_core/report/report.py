# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Optional, final

from peewee import (BooleanField, CharField, CompositeKey, ForeignKeyField,
                    ModelSelect)

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.core.utils.date_helper import DateHelper
from gws_core.entity_navigator.entity_navigator_type import (EntityType,
                                                             NavigableEntity)
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.project.model_with_project import ModelWithProject
from gws_core.report.report_dto import ReportDTO, ReportFullDTO
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User

from ..core.model.base_model import BaseModel
from ..core.model.db_field import BaseDTOField, DateTimeUTC, JSONField
from ..core.model.model_with_user import ModelWithUser
from ..experiment.experiment import Experiment
from ..lab.lab_config_model import LabConfigModel
from ..project.project import Project


@final
class Report(ModelWithUser, ModelWithProject, NavigableEntity):
    title = CharField()

    content: RichTextDTO = BaseDTOField(RichTextDTO, null=True)
    old_content = JSONField(null=True)

    project: Project = ForeignKeyField(Project, null=True)

    lab_config: LabConfigModel = ForeignKeyField(LabConfigModel, null=True)

    is_validated: bool = BooleanField(default=False)
    validated_at = DateTimeUTC(null=True)
    validated_by = ForeignKeyField(User, null=True, backref='+')

    # Date of the last synchronisation with space, null if never synchronised
    last_sync_at = DateTimeUTC(null=True)
    last_sync_by = ForeignKeyField(User, null=True, backref='+')

    is_archived = BooleanField(default=False, index=True)

    _table_name = 'gws_report'

    def get_content_as_rich_text(self) -> RichText:
        return RichText(self.content)

    def update_content_rich_text(self, rich_text: RichText) -> None:
        self.content = rich_text.get_content()

    def check_is_updatable(self) -> None:
        """Throw an error if the report is not updatable
        """
        # check experiment status
        if self.is_validated:
            raise BadRequestException(GWSException.REPORT_VALIDATED.value, GWSException.REPORT_VALIDATED.name)
        if self.is_archived:
            raise BadRequestException(
                detail="The report is archived, please unachived it to update it")

    def to_dto(self) -> ReportDTO:
        return ReportDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            title=self.title,
            project=self.project.to_dto() if self.project else None,
            is_validated=self.is_validated,
            validated_at=self.validated_at,
            validated_by=self.validated_by.to_dto() if self.validated_by else None,
            last_sync_at=self.last_sync_at,
            last_sync_by=self.last_sync_by.to_dto() if self.last_sync_by else None,
            is_archived=self.is_archived
        )

    # TODO make a separate route to get content
    def to_full_dto(self) -> ReportFullDTO:
        return ReportFullDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            title=self.title,
            project=self.project.to_dto() if self.project else None,
            is_validated=self.is_validated,
            validated_at=self.validated_at,
            validated_by=self.validated_by.to_dto() if self.validated_by else None,
            last_sync_at=self.last_sync_at,
            last_sync_by=self.last_sync_by.to_dto() if self.last_sync_by else None,
            is_archived=self.is_archived,
            content=self.content
        )

    def validate(self) -> None:
        self.is_validated = True
        self.validated_at = DateHelper.now_utc()
        self.validated_by = CurrentUserService.get_and_check_current_user()
        self.lab_config = LabConfigModel.get_current_config()

    def archive(self, archive: bool) -> 'Report':

        if self.is_archived == archive:
            return self
        self.is_archived = archive
        return self.save()

    def get_entity_name(self) -> str:
        return self.title

    def get_entity_type(self) -> EntityType:
        return EntityType.REPORT

    def entity_is_validated(self) -> bool:
        return self.is_validated

    class Meta:
        table_name = 'gws_report'


class ReportExperiment(BaseModel):
    """Many to Many relation between Report <-> Experiment

    :param BaseModel: [description]
    :type BaseModel: [type]
    :return: [description]
    :rtype: [type]
    """

    experiment = ForeignKeyField(Experiment, on_delete='CASCADE')
    report = ForeignKeyField(Report, on_delete='CASCADE')

    _table_name = 'gws_report_experiment'

    ############################################# CLASS METHODS ########################################

    @classmethod
    def create_obj(cls, experiment: Experiment, report: Report) -> 'ReportExperiment':
        report_exp: 'ReportExperiment' = ReportExperiment()
        report_exp.experiment = experiment
        report_exp.report = report
        return report_exp

    @classmethod
    def delete_obj(cls, experiment_id: str, report_id: str) -> None:
        return cls.delete().where((cls.experiment == experiment_id) & (cls.report == report_id)).execute()

    @classmethod
    def find_by_pk(cls, experiment_id: str, report_id: str) -> ModelSelect:
        return cls.select().where((cls.experiment == experiment_id) & (cls.report == report_id))

    @classmethod
    def find_reports_by_experiments(cls, experiment_ids: List[str]) -> List[Report]:
        list_: List[ReportExperiment] = list(cls.select().where(cls.experiment.in_(experiment_ids)))

        return [x.report for x in list_]

    @classmethod
    def find_experiments_by_report(cls, report_id: str) -> List[Experiment]:
        list_: List[ReportExperiment] = list(cls.select().where(cls.report == report_id))

        return [x.experiment for x in list_]

    def save(self, *args, **kwargs) -> 'BaseModel':
        """Use force insert because it is a composite key
        https://stackoverflow.com/questions/30038185/python-peewee-save-doesnt-work-as-expected

        :return: [description]
        :rtype: [type]
        """
        return super().save(*args, force_insert=True, **kwargs)

    class Meta:
        table_name = 'gws_report_experiment'
        primary_key = CompositeKey("experiment", "report")
