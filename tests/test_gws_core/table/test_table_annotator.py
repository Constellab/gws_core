from unittest import TestCase

from gws_core import Table, TableAnnotatorHelper
from gws_core.core.utils.utils import Utils
from pandas import DataFrame


# test_table_annotator
class TestTableAnnotator(TestCase):
    def test_table_row_annotator_with_indexes(self):
        dataframe = DataFrame(
            {
                "F1": {"B": 1.3, 2: 2.3, "Z": 4.5},
                "F2": {"B": 1.5, 2: 1.5, "Z": 15.1},
                "F3": {"B": 1.5, 2: 15.45, "Z": 1.35},
            }
        )
        table = Table(dataframe)

        meta_df = DataFrame(
            {
                "Gender": {2: "M", "B": "F", "E": "F"},
                "Group": {2: 1, "B": 15, "E": 15},
                "Age": {2: 18, "B": 15, "E": 15},
            }
        )
        metatable = Table(meta_df)

        # The index in table, matches the index in metatable
        # A and B rows are tagged, Z row is not tagged, tag for E are ignored
        annotated_table = TableAnnotatorHelper.annotate_rows(
            table, metatable, use_table_row_names_as_ref=True, use_metadata_row_names_as_ref=True
        )

        expected_row_tags = [
            {"Gender": "F", "Group": "15", "Age": "15"},
            {"Gender": "M", "Group": "1", "Age": "18"},
            {},
        ]

        Utils.assert_json_equals(annotated_table.get_row_tags(), expected_row_tags)

    def test_table_row_annotator_with_columns(self):
        # importer
        dataframe = DataFrame(
            {
                "sample": {0: "B", 1: 2, 2: "Z"},
                "F1": {0: 1.3, 1: 2.3, 2: 4.5},
                "F2": {0: 1.5, 1: 1.5, 2: 15.1},
                "F3": {0: 1.5, 1: 15.45, 2: 1.35},
            }
        )
        table = Table(dataframe)

        meta_df = DataFrame(
            {
                "sample_id": {0: 2, 1: "B", 2: "E"},
                "Gender": {0: "M", 1: "F", 2: "F"},
                "Group": {0: 1, 1: 15, 2: 15},
                "Age": {0: 18, 1: 15, 2: 15},
            }
        )
        metatable = Table(meta_df)

        expected_row_tags = [
            {"Gender": "F", "Group": "15", "Age": "15"},
            {"Gender": "M", "Group": "1", "Age": "18"},
            {},
        ]

        # The column sample in table, matches the column sample_id in metatable
        # A and B rows are tagged, Z row is not tagged, tag for E are ignored
        annotated_table = TableAnnotatorHelper.annotate_rows(
            table, metatable, "sample", "sample_id"
        )
        Utils.assert_json_equals(annotated_table.get_row_tags(), expected_row_tags)

        # Same test without using the column ref, it should take the first column
        annotated_table = TableAnnotatorHelper.annotate_rows(table, metatable)
        Utils.assert_json_equals(annotated_table.get_row_tags(), expected_row_tags)

    def test_table_column_annotator_with_indexes(self):
        dataframe = DataFrame(
            {
                "F1": {"B": 1.3, "A": 2.3, "Z": 4.5},
                "F2": {"B": 1.5, "A": 1.5, "Z": 15.1},
                "F3": {"B": 1.5, "A": 15.45, "Z": 1.35},
            }
        )
        table = Table(dataframe)

        meta_df = DataFrame(
            {
                "Gender": {"F2": "M", "F1": "F", "F9": "M"},
                "Group": {"F2": 1, "F1": 15, "F9": 15},
                "Age": {"F2": 18, "F1": 15, "F9": 15},
            }
        )
        metatable = Table(meta_df)

        # The column names in table, matches the index in metatable
        # F1 and F2 columns are tagged, F3 column is not tagged, tag for F9 are ignored
        annotated_table = TableAnnotatorHelper.annotate_columns(
            table, metatable, use_table_column_names_as_ref=True, use_metadata_row_names_as_ref=True
        )

        expected_columns_tags = [
            {"Gender": "F", "Group": "15", "Age": "15"},
            {"Gender": "M", "Group": "1", "Age": "18"},
            {},
        ]

        Utils.assert_json_equals(annotated_table.get_column_tags(), expected_columns_tags)

    def test_table_column_annotator_with_columns(self):
        dataframe = DataFrame(
            {
                0: {"sample": "F1", "B": 1.3, "A": 2.3, "Z": 4.5},
                1: {"sample": "F2", "B": 1.5, "A": 1.5, "Z": 15.1},
                2: {"sample": "F3", "B": 1.5, "A": 15.45, "Z": 1.35},
            }
        )

        table = Table(dataframe)

        meta_df = DataFrame(
            {
                "sample_id": {0: "F1", 1: "F2", 2: "F9"},
                "Gender": {0: "M", 1: "F", 2: "M"},
                "Group": {0: 1, 1: 15, 2: 15},
                "Age": {0: 18, 1: 15, 2: 15},
            }
        )

        metatable = Table(meta_df)

        expected_columns_tags = [
            {"Gender": "M", "Group": "1", "Age": "18"},
            {"Gender": "F", "Group": "15", "Age": "15"},
            {},
        ]

        # The column names in table, matches the column names in metatable
        # F1 and F2 columns are tagged, F3 column is not tagged, tag for F9 are ignored
        annotated_table = TableAnnotatorHelper.annotate_columns(
            table, metatable, "sample", "sample_id"
        )

        Utils.assert_json_equals(annotated_table.get_column_tags(), expected_columns_tags)

        # Same test without using the column ref, it should take the first column/row
        annotated_table = TableAnnotatorHelper.annotate_columns(table, metatable)

        Utils.assert_json_equals(annotated_table.get_column_tags(), expected_columns_tags)
