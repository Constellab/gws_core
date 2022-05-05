# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import final

from peewee import (BooleanField, CharField, CompositeKey, ForeignKeyField,
                    ModelSelect)

from ..core.model.base_model import BaseModel
from ..core.model.db_field import JSONField
from ..core.model.model_with_user import ModelWithUser
from ..experiment.experiment import Experiment
from ..lab.lab_config_model import LabConfigModel
from ..model.typing_register_decorator import typing_registrator
from ..project.project import Project


@final
@typing_registrator(unique_name="Report", object_type="MODEL", hide=True)
class Report(ModelWithUser):
    title = CharField()

    content = JSONField(null=True)

    project: Project = ForeignKeyField(Project, null=True)

    is_validated: bool = BooleanField(default=False)

    lab_config: LabConfigModel = ForeignKeyField(LabConfigModel, null=True)

    _table_name = 'gws_report'

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        json_ = super().to_json(deep=deep, **kwargs)

        if self.project:
            json_["project"] = {
                'id': self.project.id,
                'title': self.project.title
            }

        if not deep:
            del json_["content"]

        return json_

    def validate(self) -> None:
        self.is_validated = True
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
