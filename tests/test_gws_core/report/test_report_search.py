

from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchParams
from gws_core.document.document_dto import DocumentSaveDTO
from gws_core.report.report_service import ReportService
from gws_core.test.base_test_case import BaseTestCase


# test_report_search
class TestReportSearch(BaseTestCase):

    def test_report_search(self):
        report_1 = ReportService.create(DocumentSaveDTO(title='The first report'))
        ReportService.create(DocumentSaveDTO(title='Another text to explain experiment'))

        search_dict: SearchParams = SearchParams()

        # Test title search
        search_dict.filtersCriteria = [{"key": "title", "operator": "CONTAINS", "value": "first"}]
        self._search(search_dict, 1)

        # test search name
        paginator: Paginator = ReportService.search_by_name('first')
        self.assertEqual(paginator.page_info.total_number_of_items, 1)
        self.assertEqual(paginator.results[0].id, report_1.id)

    def _search(self, search_dict: SearchParams, expected_nb_of_result: int) -> None:
        paginator = ReportService.search(search_dict).to_dto()
        self.assertEqual(paginator.total_number_of_items, expected_nb_of_result)
