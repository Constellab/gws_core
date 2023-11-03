# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import final

from peewee import (BooleanField, CharField, CompositeKey, ForeignKeyField,
                    ModelSelect)

from gws_core.core.classes.rich_text_content import RichText
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.core.utils.date_helper import DateHelper
from gws_core.project.model_with_project import ModelWithProject
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User

from ..core.model.base_model import BaseModel
from ..core.model.db_field import DateTimeUTC, JSONField
from ..core.model.model_with_user import ModelWithUser
from ..experiment.experiment import Experiment
from ..lab.lab_config_model import LabConfigModel
from ..project.project import Project


@final
class Report(ModelWithUser, ModelWithProject):
    title = CharField()

    content = JSONField(null=True)

    project: Project = ForeignKeyField(Project, null=True)

    lab_config: LabConfigModel = ForeignKeyField(LabConfigModel, null=True)

    is_validated: bool = BooleanField(default=False)
    validated_at = DateTimeUTC(null=True)
    validated_by = ForeignKeyField(User, null=True, backref='+')

    # Date of the last synchronisation with space, null if never synchronised
    last_sync_at = DateTimeUTC(null=True)
    last_sync_by = ForeignKeyField(User, null=True, backref='+')

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

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        json_ = super().to_json(deep=deep, **kwargs)

        if self.project:
            json_["project"] = {
                'id': self.project.id,
                'code': self.project.code,
                'title': self.project.title
            }

        if self.validated_by:
            json_["validated_by"] = self.validated_by.to_json()

        if self.last_sync_by:
            json_["last_sync_by"] = self.last_sync_by.to_json()

        if not deep:
            del json_["content"]

        return json_

    def validate(self) -> None:
        self.is_validated = True
        self.validated_at = DateHelper.now_utc()
        self.validated_by = CurrentUserService.get_and_check_current_user()
        self.lab_config = LabConfigModel.get_current_config()


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

    def save(self, *args, **kwargs) -> 'BaseModel':
        """Use force insert because it is a composite key
        https://stackoverflow.com/questions/30038185/python-peewee-save-doesnt-work-as-expected

        :return: [description]
        :rtype: [type]
        """
        return super().save(*args, force_insert=True, **kwargs)

    class Meta:
        primary_key = CompositeKey("experiment", "report")
