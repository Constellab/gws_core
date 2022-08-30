# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from peewee import CompositeKey, ForeignKeyField, ModelSelect

from ..core.model.base_model import BaseModel
from ..resource.resource_model import ResourceModel
from .report import Report


class ReportResource(BaseModel):
    """Model to store which resources are used in reports"""

    report: Report = ForeignKeyField(Report, null=False, index=True, on_delete='CASCADE')
    resource: ResourceModel = ForeignKeyField(ResourceModel, null=False, index=True, on_delete='CASCADE')

    _table_name = 'gws_report_resource'

    @classmethod
    def get_by_report(cls, report_id: str) -> List['ReportResource']:
        return list(ReportResource.select().where(ReportResource.report == report_id))

    @classmethod
    def get_by_resource(cls, resource_id: str) -> ModelSelect:
        return ReportResource.select().where(ReportResource.resource == resource_id)

    def save(self, *args, **kwargs) -> 'BaseModel':
        """Use force insert because it is a composite key
        https://stackoverflow.com/questions/30038185/python-peewee-save-doesnt-work-as-expected

        :return: [description]
        :rtype: [type]
        """
        return super().save(*args, force_insert=True, **kwargs)

    class Meta:
        primary_key = CompositeKey("report", "resource")
