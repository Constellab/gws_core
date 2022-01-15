
from gws_core import BaseTestCase, ViewTester
from gws_core.extra import DataProvider, TableHeatmapView


class TestTableHeatmapView(BaseTestCase):

    def test_heatmap_view(self,):
        table = DataProvider.get_iris_table()
        tester = ViewTester(
            view=TableHeatmapView(table)
        )
        view_dict = tester.to_dict({
            "from_row": 1,
            "number_of_rows_per_page": 50,
            "from_column": 1,
            "number_of_columns_per_page": 4,
        })
        self.assertEqual(view_dict["type"], "heatmap-view")
        self.assertEqual(
            view_dict["data"],
            table.to_dataframe().iloc[0:50, 0:4].to_dict('list')
        )
