
from gws_core import BaseTestCase, TableVennDiagramView, ViewTester
from tests.gws_core_test_helper import GWSCoreTestHelper


class TestVennDiagrammView(BaseTestCase):

    def test_venn_diagram_view(self,):
        table = GWSCoreTestHelper.get_venn_data_table()
        tester = ViewTester(
            view=TableVennDiagramView(table)
        )
        dic = tester.to_dict({})

        self.assertEqual(dic["data"]["total_number_of_groups"], 3)
        self.assertEqual(len(dic["data"]["sections"]), 7)
        self.assertEqual(dic["data"]["sections"][6], {'group_names': ['A', 'B', 'C'], 'data': {'3', '1'}})

        dic = tester.to_dict({"column_names": ["A", "B"]})
        self.assertEqual(dic["data"]["total_number_of_groups"], 2)
        self.assertEqual(len(dic["data"]["sections"]), 3)

        dic = tester.to_dict({"column_names": ["A", "B", "D", "E"]})
        self.assertEqual(len(dic["data"]["sections"]), 15)
