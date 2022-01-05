
from gws_core import BaseTestCase, TableVennDiagramView, ViewTester
from gws_core_test_helper import GWSCoreTestHelper


class TestVennDiagrammView(BaseTestCase):

    def test_venn_diagram_view(self,):
        table = GWSCoreTestHelper.get_venn_data_table()
        tester = ViewTester(
            view=TableVennDiagramView(table)
        )
        dic = tester.to_dict({})

        print(dic)

        self.assertEqual(dic["data"]["total_number_of_groups"], 3)
        self.assertEqual(len(dic["data"]["sections"]), 7)
        self.assertEqual(dic["data"]["sections"][6], {'group_names': ['A', 'B', 'C'], 'data': {'3', '1'}})

        dic = tester.to_dict({
            "series": [
                {"data_column": "A"},
                {"data_column": "B"}
            ]
        })
        self.assertEqual(dic["data"]["total_number_of_groups"], 2)
        self.assertEqual(len(dic["data"]["sections"]), 3)

        dic = tester.to_dict({
            "series": [
                {"data_column": "A"},
                {"data_column": "B"},
                {"data_column": "D"},
                {"data_column": "E"}
            ]
        })
        self.assertEqual(len(dic["data"]["sections"]), 15)
