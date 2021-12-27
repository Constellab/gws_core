from gws_core import (BaseTestCase, ConfigParams, Dataset, DatasetImporter,
                      DatasetView, File, TaskRunner, ViewTester)
from gws_core.extra import DataProvider


class TestDatasetView(BaseTestCase):

    async def test_dataset_view(self,):
        self.print("Dataset import")
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

        self.assertEqual(dic["type"], "dataset-view")
        self.assertEqual(
            dic["data"],
            ds.get_data().iloc[0:50, :].to_dict('list')
        )

        self.assertEqual(dic["target_names"], ['variety'])
