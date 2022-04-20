

from gws_core.core.classes.search_builder import SearchParams
from gws_core.report.report import Report
from gws_core.report.report_service import ReportService
from gws_core.test.base_test_case import BaseTestCase


class TestReportSearch(BaseTestCase):

    def test_report_search(self):
        ReportService.create({'title': 'The first report'})
        ReportService.create({'title': 'Another text to explain experiment'})

        search_dict: SearchParams = SearchParams()

        # Test full text search
        search_dict.filtersCriteria = [{"key": "title", "operator": "CONTAINS", "value": "first"}]
        self._search(search_dict, 1)

    def _search(self, search_dict: SearchParams, expected_nb_of_result: int) -> None:
        paginator = ReportService.search(search_dict).to_json()
        self.assertEqual(paginator['total_number_of_items'], expected_nb_of_result)
