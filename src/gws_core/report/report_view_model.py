# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from peewee import CompositeKey, ForeignKeyField, ModelSelect

from gws_core.core.model.base_model import BaseModel
from gws_core.resource.view_config.view_config import ViewConfig

from .report import Report


class ReportViewModel(BaseModel):
    """Model to store which views are used in reports"""

    report: Report = ForeignKeyField(Report, null=False, index=True, on_delete='CASCADE')
    view: ViewConfig = ForeignKeyField(ViewConfig, null=False, index=True, on_delete='RESTRICT')

    _table_name = 'gws_report_view'

    @classmethod
    def get_by_report(cls, report_id: str) -> List['ReportViewModel']:
        return list(ReportViewModel.select().where(ReportViewModel.report == report_id))

    @classmethod
    def get_by_reports(cls, report_ids: List[str]) -> ModelSelect:
        return ReportViewModel.select().where(ReportViewModel.report.in_(report_ids))

    @classmethod
    def get_by_view(cls, view_config_id: str) -> ModelSelect:
        return ReportViewModel.select().where(ReportViewModel.view == view_config_id)

    @classmethod
    def get_by_views(cls, view_config_ids: List[str]) -> ModelSelect:
        return ReportViewModel.select().where(
            ReportViewModel.view.in_(view_config_ids))

    @classmethod
    def get_by_resource(cls, resource_id: str) -> ModelSelect:
        return ReportViewModel.select().join(
            ViewConfig, on=(ReportViewModel.view == ViewConfig.id)).join(
            Report, on=(ReportViewModel.report == Report.id)).where(
            ReportViewModel.view.resource_model == resource_id).order_by(
            ReportViewModel.report.last_modified_at.desc())

    @classmethod
    def get_by_resources(cls, resource_ids: List[str]) -> ModelSelect:
        return ReportViewModel.select().join(
            ViewConfig, on=(ReportViewModel.view == ViewConfig.id)).join(
            Report, on=(ReportViewModel.report == Report.id)).where(
            ReportViewModel.view.resource_model.in_(resource_ids)).order_by(
            ReportViewModel.report.last_modified_at.desc())

    def save(self, *args, **kwargs) -> 'BaseModel':
        """Use force insert because it is a composite key
        https://stackoverflow.com/questions/30038185/python-peewee-save-doesnt-work-as-expected

        :return: [description]
        :rtype: [type]
        """
        return super().save(*args, force_insert=True, **kwargs)

    class Meta:
        primary_key = CompositeKey("report", "view")
