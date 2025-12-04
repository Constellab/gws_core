from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchFilterCriteria, SearchOperator, SearchParams
from gws_core.note.note_dto import NoteSaveDTO
from gws_core.note.note_service import NoteService
from gws_core.test.base_test_case import BaseTestCase


# test_note_search
class TestNoteSearch(BaseTestCase):
    def test_note_search(self):
        note_1 = NoteService.create(NoteSaveDTO(title="The first note"))
        NoteService.create(NoteSaveDTO(title="Another text to explain scenario"))

        search_dict: SearchParams = SearchParams()

        # Test title search
        search_dict.set_filters_criteria(
            [SearchFilterCriteria(key="title", operator=SearchOperator.CONTAINS, value="first")]
        )
        self._search(search_dict, 1)

        # test search name
        paginator: Paginator = NoteService.search_by_name("first")
        self.assertEqual(paginator.page_info.total_number_of_items, 1)
        self.assertEqual(paginator.results[0].id, note_1.id)

    def _search(self, search_dict: SearchParams, expected_nb_of_result: int) -> None:
        paginator = NoteService.search(search_dict).to_dto()
        self.assertEqual(paginator.total_number_of_items, expected_nb_of_result)
