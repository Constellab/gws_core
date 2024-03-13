

from unittest import TestCase

from gws_core import ViewTester, ViewType
from gws_core.extra import DataProvider, TableHeatmapView
from gws_core.impl.table.view.table_selection import Serie1d


# test_heatmap_view
class TestTableHeatmapView(TestCase):

    def test_heatmap_view(self,):
        table = DataProvider.get_iris_table()
        tester = ViewTester(
            view=TableHeatmapView(table)
        )

        # 1 series with all columns
        serie: Serie1d = {"name": "first", "y": {"type": "columns", "selection": [
            "sepal_length",  "sepal_width", "petal_length", "petal_width"]}}

        view_dto = tester.to_dto({"serie": serie})
        self.assertEqual(view_dto.type, ViewType.HEATMAP)
        self.assertEqual(
            view_dto.data["table"],
            table.to_dataframe().iloc[0:, 0:4].to_dict('split')["data"]
        )
