

from typing import List

from peewee import CompositeKey, ForeignKeyField, ModelSelect

from gws_core.report.report import Report

from ..core.model.base_model import BaseModel
from ..experiment.experiment import Experiment


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
    def find_reports_by_experiments(cls, experiment_id: List[str]) -> List[Report]:
        list_: List[ReportExperiment] = list(cls.select().where(cls.experiment.in_(experiment_id)))

        return [x.report for x in list_]

    @classmethod
    def find_synced_reports_by_experiment(cls, experiment_id: str) -> List[Report]:
        list_: List[ReportExperiment] = list(cls.select().where(
            (cls.experiment == experiment_id) & (cls.report.last_sync_at.is_null(False)))
            .join(Report)
        )

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
