from gws_core import BaseTestCase, Dataset
from gws_core.extra import DataProvider
from pandas import DataFrame


class TestImporter(BaseTestCase):

    def test_importer(self):
        ds = DataProvider.get_iris_dataset()

        self.assertEquals(ds.nb_features, 4)
        self.assertEquals(ds.nb_targets, 1)
        self.assertEquals(ds.nb_instances, 150)
        self.assertEquals(ds.get_features().values[0, 0], 5.1)
        self.assertEquals(ds.get_features().values[0, 1], 3.5)
        self.assertEquals(ds.get_features().values[149, 0], 5.9)
        self.assertEquals(list(ds.feature_names), ["sepal.length", "sepal.width", "petal.length", "petal.width"])
        self.assertEquals(list(ds.target_names), ["variety"])

        ds.convert_targets_to_dummy_matrix()

    def test_data_select(self):
        ds = DataProvider.get_iris_dataset()

        selected_ds: Dataset = ds.select_by_column_positions([1, 2])
        self.assertEqual(selected_ds.feature_names, ["sepal.width", "petal.length"])
        self.assertEqual(selected_ds.target_names, [])
        self.assertEqual(selected_ds.nb_rows, 150)

        selected_ds = ds.select_by_column_positions([1, 2, 4])
        self.assertEqual(selected_ds.feature_names, ["sepal.width", "petal.length"])
        self.assertEqual(selected_ds.target_names, ["variety"])
        self.assertEqual(selected_ds.nb_rows, 150)

        selected_ds = ds.select_by_column_names([{"name": ["sepal.width", "petal.length", "variety"]}])
        self.assertEqual(selected_ds.feature_names, ["sepal.width", "petal.length"])
        self.assertEqual(selected_ds.target_names, ["variety"])
        self.assertEqual(selected_ds.nb_rows, 150)

        selected_ds = ds.select_by_row_positions([1, 2, 4])
        self.assertEqual(selected_ds.feature_names, ["sepal.length", "sepal.width", "petal.length", "petal.width"])
        self.assertEqual(selected_ds.target_names, ["variety"])
        self.assertEqual(selected_ds.nb_rows, 3)

    def test_importer_no_head(self):
        ds = DataProvider.get_no_head_iris_dataset()
        self.assertEquals(ds.nb_features, 4)
        self.assertEquals(ds.nb_targets, 1)
        self.assertEquals(ds.nb_instances, 150)
        self.assertEquals(ds.get_features().values[0, 0], 5.1)
        self.assertEquals(ds.get_features().values[0, 1], 3.5)
        self.assertEquals(ds.get_features().values[149, 0], 5.9)
        self.assertEquals(list(ds.feature_names), ['0', '1', '2', '3'])
        self.assertEquals(list(ds.target_names), ['4'])
        #self.assertEquals(list(ds.feature_names), ["C0", "C1", "C2", "C3"])
        #self.assertEquals(list(ds.target_names), ["C4"])

    def test_table_dummy_matrix(self):
        meta = {
            "row_tags": [
                {"lg": "EN", "c": "US", "user": "Vi"},
                {"lg": "JP", "c": "JP", "user": "Jo"},
                {"lg": "FR", "c": "FR", "user": "Jo"},
                {"lg": "JP", "c": "JP", "user": "Vi"},
            ],
            "column_tags": [
                {"lg": "EN", "c": "UK"},
                {"lg": "PT", "c": "PT"},
                {"lg": "CH", "c": "CH"}
            ],
        }

        dataset: Dataset = Dataset(
            data=[[1, 2, 3], [3, 4, 6], [3, 7, 6], [3, 7, 6]],
            row_names=["NY", "Tokyo", "Paris", "Kyoto"],
            column_names=["London", "Lisboa", "Beijin"],
            meta=meta
        )
        data = dataset.convert_row_tags_to_dummy_target_matrix(key="lg")

        dummy = DataFrame(data=[
            [1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ],
            index=["EN", "JP", "FR", "JP"],
            columns=["EN", "FR", "JP"]
        )
        self.assertTrue(data.equals(dummy))
