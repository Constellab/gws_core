from gws_core import BaseTestCase, TableBoxPlotView, ViewTester
from gws_core.extra import DataProvider


class TestTableBoxPlotView(BaseTestCase):

    def test_boxplot_view(self,):
        table = DataProvider.get_iris_table()
        tester = ViewTester(
            view=TableBoxPlotView(table)
        )

        dic = tester.to_dict({
            "series": [
                {
                    "y_data_columns": ["petal.length", "petal.width"]
                }
            ]
        })
        self.assertEqual(dic["type"], "box-plot-view")
        self.assertEqual(dic["data"]["x_tick_labels"], ['petal.length', 'petal.width'])
        self.assertEqual(dic["data"]["series"][0]["data"]["x"], [0, 1])
        self.assertEqual(dic["data"]["series"][0]["data"]["min"], [1.0, 0.1])
        self.assertEqual(dic["data"]["series"][0]["data"]["q1"], [1.6, 0.3])
        self.assertEqual(dic["data"]["series"][0]["data"]["median"], [4.35, 1.3])
        self.assertEqual(dic["data"]["series"][0]["data"]["q3"], [5.1, 1.8])
        self.assertEqual(dic["data"]["series"][0]["data"]["max"], [6.9, 2.5])

    def test_boxplot_view_without_params(self,):
        table = DataProvider.get_iris_table()
        tester = ViewTester(
            view=TableBoxPlotView(table)
        )

        dic = tester.to_dict({
            "series": []
        })
        self.assertEqual(dic["type"], "box-plot-view")
        self.assertEqual(dic["data"]["x_tick_labels"], ['sepal.length', 'sepal.width', 'petal.length'])
        self.assertEqual(dic["data"]["series"][0]["data"]["x"], [0, 1, 2])
        self.assertEqual(dic["data"]["series"][0]["data"]["min"], [4.3, 2.0, 1.0])
        self.assertEqual(dic["data"]["series"][0]["data"]["q1"], [5.1, 2.8, 1.6])
        self.assertEqual(dic["data"]["series"][0]["data"]["median"], [5.8, 3.0, 4.35])
        self.assertEqual(dic["data"]["series"][0]["data"]["q3"], [6.4, 3.3, 5.1])
        self.assertEqual(dic["data"]["series"][0]["data"]["max"], [7.9, 4.4, 6.9])
