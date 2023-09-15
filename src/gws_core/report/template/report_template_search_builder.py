# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.core.classes.search_builder import SearchBuilder
from gws_core.report.report import Report
from gws_core.report.template.report_template import ReportTemplate


class ReportTemplateSearchBuilder(SearchBuilder):
    def __init__(self) -> None:
        super().__init__(ReportTemplate, default_orders=[ReportTemplate.last_modified_at.desc()])
