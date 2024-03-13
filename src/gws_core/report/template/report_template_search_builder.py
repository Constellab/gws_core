

from gws_core.core.classes.search_builder import SearchBuilder
from gws_core.report.report import Report
from gws_core.report.template.report_template import ReportTemplate


class ReportTemplateSearchBuilder(SearchBuilder):
    def __init__(self) -> None:
        super().__init__(ReportTemplate, default_orders=[ReportTemplate.last_modified_at.desc()])
