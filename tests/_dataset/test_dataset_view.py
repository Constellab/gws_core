from gws_core import BaseTestCase, ViewTester, ViewType
from gws_core.extra import DataProvider, DatasetView


class TestDatasetView(BaseTestCase):

    def test_dataset_view(self,):
        ds = DataProvider.get_iris_dataset()
        tester = ViewTester(
            view=DatasetView(ds)
        )
        dic = tester.to_dict(dict(
            from_row=1,
            number_of_rows_per_page=50,
            from_column=1,
            number_of_columns_per_page=50
        ))

        self.assertEqual(dic["type"], ViewType.DATASET.value)
        self.assertEqual(
            dic["data"]["table"],
            ds.get_data().iloc[0:50, :].to_dict('split')["data"]
        )

        self.assertEqual(dic["data"]["target_names"], ['variety'])
