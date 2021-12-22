# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Dict, List

from gws_core.core.exception.gws_exceptions import GWSException
from peewee import ModelSelect

from ..core.classes.paginator import Paginator
from ..core.classes.search_builder import SearchBuilder, SearchDict
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..experiment.experiment import Experiment
from ..report.report_dto import ReportDTO
from ..report.report_search_builder import ReportSearchBuilder
from .report import Report, ReportExperiment


class ReportService():

    @classmethod
    @transaction()
    def create(cls, report_dto: ReportDTO, experiment_ids: List[str] = None) -> Report:
        report = Report()
        report.title = report_dto["title"]
        report.save()

        if experiment_ids is not None:
            # Create the ReportExperiment
            for experiment_id in experiment_ids:
                experiment: Experiment = Experiment.get_by_id_and_check(experiment_id)

                ReportExperiment.create_obj(experiment, report).save()

        return report

    @classmethod
    def update(cls, report_id: str, report_dto: ReportDTO) -> Report:
        report: Report = cls._get_and_check_before_update(report_id)

        report.title = report_dto['title']
        return report.save()

    @classmethod
    def update_content(cls, report_id: str, report_content: Dict) -> Report:
        report: Report = cls._get_and_check_before_update(report_id)

        report.content = report_content
        return report.save()

    @classmethod
    def delete(cls, report_id: str) -> None:
        cls._get_and_check_before_update(report_id)

        Report.delete_by_id(report_id)

    @classmethod
    def validate(cls, report_id: str) -> Report:
        report: Report = cls._get_and_check_before_update(report_id)

        # check that all associated experiment are validated
        experiments: List[Experiment] = cls.get_experiments_by_report(report_id)
        for experiment in experiments:
            if not experiment.is_validated:
                raise BadRequestException(GWSException.REPORT_VALIDATION_EXP_NOT_VALIDATED.value,
                                          GWSException.REPORT_VALIDATION_EXP_NOT_VALIDATED.name)

        report.is_validated = True

        return report.save()

    @classmethod
    def add_experiment(cls, report_id: str, experiment_id: str) -> Experiment:
        report: Report = cls._get_and_check_before_update(report_id)

        if ReportExperiment.find_by_pk(experiment_id, report_id).count() > 0:
            raise BadRequestException(GWSException.REPORT_EXP_ALREADY_ASSOCIATED.value,
                                      GWSException.REPORT_EXP_ALREADY_ASSOCIATED.name)

        experiment: Experiment = Experiment.get_by_id_and_check(experiment_id)

        ReportExperiment.create_obj(experiment, report).save()
        return experiment

    @classmethod
    def remove_experiment(cls, report_id: str, experiment_id: str) -> None:
        cls._get_and_check_before_update(report_id)

        ReportExperiment.delete_obj(experiment_id, report_id)

    @classmethod
    def _get_and_check_before_update(cls, report_id: str) -> Report:
        """Retrieve the report and check if it's updatable or deletable

        :param report_id: [description]
        :type report_id: str
        :raises BadRequestException: [description]
        :return: [description]
        :rtype: Report
        """
        report: Report = Report.get_by_id_and_check(report_id)

        if report.is_validated:
            raise BadRequestException(GWSException.REPORT_VALIDATED.value, GWSException.REPORT_VALIDATED.name)

        return report

    ################################################# GET ########################################

    @classmethod
    def get_by_id_and_check(cls, id: str) -> Report:
        return Report.get_by_id_and_check(id)

    @classmethod
    def get_by_experiment(cls, experiment_id: str) -> List[Report]:
        return list(Report.select().join(ReportExperiment).where(
            ReportExperiment.experiment == experiment_id).order_by(
            Report.last_modified_at.desc()))

    @classmethod
    def get_experiments_by_report(cls, report_id: str) -> List[Experiment]:
        return list(Experiment.select().join(ReportExperiment).where(
            ReportExperiment.report == report_id).order_by(
            Experiment.last_modified_at.desc()))

    @classmethod
    def search(cls,
               search: SearchDict,
               page: int = 0,
               number_of_items_per_page: int = 20) -> Paginator[Report]:

        search_builder: SearchBuilder = ReportSearchBuilder()

        model_select: ModelSelect = search_builder.build_search(search)
        return Paginator(
            model_select, page=page, number_of_items_per_page=number_of_items_per_page)
