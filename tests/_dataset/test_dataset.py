from gws_core import (BaseTestCase, Dataset, DatasetImporter, File, Settings,
                      TaskRunner)
from gws_core.extra import DataProvider


class TestImporter(BaseTestCase):

    async def test_importer(self):
        self.print("Dataset import")
        ds = DataProvider.get_iris_dataset()
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
        ds = DataProvider.get_iris_dataset()
        print(ds)

        selected_ds = ds.select_by_column_positions([1, 2])
        self.assertEqual(selected_ds.feature_names, ["sepal.width", "petal.length"])
        self.assertEqual(selected_ds.target_names, [])
        self.assertEqual(selected_ds.nb_rows, 150)

        selected_ds = ds.select_by_column_positions([1, 2, 4])
        self.assertEqual(selected_ds.feature_names, ["sepal.width", "petal.length"])
        self.assertEqual(selected_ds.target_names, ["variety"])
        self.assertEqual(selected_ds.nb_rows, 150)

        selected_ds = ds.select_by_column_names(["sepal.width", "petal.length", "variety"])
        self.assertEqual(selected_ds.feature_names, ["sepal.width", "petal.length"])
        self.assertEqual(selected_ds.target_names, ["variety"])
        self.assertEqual(selected_ds.nb_rows, 150)

        selected_ds = ds.select_by_row_positions([1, 2, 4])
        self.assertEqual(selected_ds.feature_names, ["sepal.length", "sepal.width", "petal.length", "petal.width"])
        self.assertEqual(selected_ds.target_names, ["variety"])
        self.assertEqual(selected_ds.nb_rows, 3)

    async def test_importer_no_head(self):
        self.print("Dataset import without header")
        ds = DataProvider.get_no_head_iris_dataset()
        self.assertEquals(ds.nb_features, 4)
        self.assertEquals(ds.nb_targets, 1)
        self.assertEquals(ds.nb_instances, 150)
        self.assertEquals(ds.get_features().values[0, 0], 5.1)
        self.assertEquals(ds.get_features().values[0, 1], 3.5)
        self.assertEquals(ds.get_features().values[149, 0], 5.9)
        self.assertEquals(list(ds.feature_names), ["C0", "C1", "C2", "C3"])
        self.assertEquals(list(ds.target_names), ["C4"])
        print(ds)
