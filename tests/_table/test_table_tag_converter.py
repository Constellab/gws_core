from gws_core import BaseTestCase, Table
from gws_core.extra import DataProvider
from pandas import DataFrame


class TestTableTagConverter(BaseTestCase):

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

        table = Table(
            data=[[1, 2, 3], [3, 4, 6], [3, 7, 6], [3, 7, 6]],
            row_names=["NY", "Tokyo", "Paris", "Kyoto"],
            column_names=["London", "Lisboa", "Beijin"],
            meta=meta
        )
