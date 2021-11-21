import os

from gws_core import (BaseTestCase, ConfigParams, Dataset, DatasetImporter,
                      DatasetView, File, Settings, TaskRunner, ViewTester)


class TestTDatasetView(BaseTestCase):

    async def test_dataset_view(self,):
        self.print("Dataset import")
        settings = Settings.retrieve()
        test_dir = settings.get_variable("gws_core:testdata_dir")
        # run trainer
        tester = TaskRunner(
            params={
                "delimiter": ",",
                "header": 0,
                "targets": ["variety"]
            },
            inputs={'file': File(path=os.path.join(test_dir, "./iris.csv"))},
            task_type=DatasetImporter
        )
        outputs = await tester.run()
        ds = outputs['resource']

        tester = ViewTester(
            view=DatasetView(ds)
        )
        dic = tester.to_dict({})

        self.assertEqual(dic["type"], "dataset-view")
        self.assertEqual(
            dic["data"],
            ds.get_data().iloc[0:49, 0:4].to_dict('list')
        )

        self.assertEqual(
            dic["targets"],
            ds.get_targets().iloc[0:49, :].to_dict('list')
        )
