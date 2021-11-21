
import asyncio
import os

from gws_core import (BaseTestCase, Dataset, DatasetImporter, File, Settings,
                      TaskRunner)


class TestImporter(BaseTestCase):

    async def test_importer(self):
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
            inputs={"file": File(path=os.path.join(test_dir, "./iris.csv"))},
            task_type=DatasetImporter
        )
        outputs = await tester.run()
        ds = outputs['resource']
        self.assertEquals(ds.nb_features, 4)
        self.assertEquals(ds.nb_targets, 1)
        self.assertEquals(ds.nb_instances, 150)
        self.assertEquals(ds.get_features().values[0, 0], 5.1)
        self.assertEquals(ds.get_features().values[0, 1], 3.5)
        self.assertEquals(ds.get_features().values[149, 0], 5.9)
        self.assertEquals(list(ds.feature_names), ["sepal.length", "sepal.width", "petal.length", "petal.width"])
        self.assertEquals(list(ds.target_names), ["variety"])

        y = ds.convert_targets_to_dummy_matrix()
        print(y)

    async def test_data_select(self):
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
            inputs={"file": File(path=os.path.join(test_dir, "./iris.csv"))},
            task_type=DatasetImporter
        )
        outputs = await tester.run()
        ds = outputs['resource']
        print(ds)

        selected_ds = ds.select_by_column_indexes([1, 2])
        self.assertEqual(selected_ds.feature_names, ["sepal.width", "petal.length"])
        self.assertEqual(selected_ds.target_names, [])
        self.assertEqual(selected_ds.nb_rows, 150)

        selected_ds = ds.select_by_column_indexes([1, 2, 4])
        self.assertEqual(selected_ds.feature_names, ["sepal.width", "petal.length"])
        self.assertEqual(selected_ds.target_names, ["variety"])
        self.assertEqual(selected_ds.nb_rows, 150)

        selected_ds = ds.select_by_column_indexes([1, 2, 4], only_targets=True)
        self.assertEqual(selected_ds.feature_names, [])
        self.assertEqual(selected_ds.target_names, ["variety"])
        self.assertEqual(selected_ds.nb_rows, 150)

        selected_ds = ds.select_by_row_indexes([1, 2, 4])
        self.assertEqual(selected_ds.feature_names, ["sepal.length", "sepal.width", "petal.length", "petal.width"])
        self.assertEqual(selected_ds.target_names, ["variety"])
        self.assertEqual(selected_ds.nb_rows, 3)

    async def test_importer_no_head(self):
        self.print("Dataset import without header")
        settings = Settings.retrieve()
        test_dir = settings.get_variable("gws_core:testdata_dir")
        # run trainer
        tester = TaskRunner(
            params={
                "delimiter": ",",
                "header": -1,
                "targets": [4]
            },
            inputs={"file": File(path=os.path.join(test_dir, "./iris_no_head.csv"))},
            task_type=DatasetImporter
        )
        outputs = await tester.run()
        ds = outputs['resource']
        self.assertEquals(ds.nb_features, 4)
        self.assertEquals(ds.nb_targets, 1)
        self.assertEquals(ds.nb_instances, 150)
        self.assertEquals(ds.get_features().values[0, 0], 5.1)
        self.assertEquals(ds.get_features().values[0, 1], 3.5)
        self.assertEquals(ds.get_features().values[149, 0], 5.9)
        self.assertEquals(list(ds.feature_names), list(range(0, 4)))
        self.assertEquals(list(ds.target_names), [4])
        print(ds)
