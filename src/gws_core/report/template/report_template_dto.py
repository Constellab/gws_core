# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO


class ReportTemplateDTO(ModelWithUserDTO):
    title: str


class ReportTemplateFullDTO(ReportTemplateDTO):
    content: dict


class CreateReportTemplateDTO(BaseModelDTO):
    title: str


class CreateReportTemplateFromReportDTO(BaseModelDTO):
    report_id: str
