

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO


class ReportTemplateDTO(ModelWithUserDTO):
    title: str


class CreateReportTemplateDTO(BaseModelDTO):
    title: str


class CreateReportTemplateFromReportDTO(BaseModelDTO):
    report_id: str
