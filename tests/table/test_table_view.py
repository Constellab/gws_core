import inspect
import os
from typing import List

from gws_core import (BaseTestCase, Resource, ResourceService, Robot, Settings,
                      Table, TableView, resource_decorator, view)
from pandas import DataFrame


class TestTableView(BaseTestCase):

    def test_table_view(self,):
        settings = Settings.retrieve()
        testdata_dir = settings.get_variable("gws_core:testdata_dir")
        file_path = os.path.join(testdata_dir, "iris.csv")
        table = Table.import_from_path(file_path, delimiter=",", head=0)
        vw = TableView(table)

        self.assertEqual(
            vw._slice(from_row_index=4, to_row_index=21, from_column_index=1, to_column_index=4),
            table.to_table().iloc[4:21, 1:4].to_dict()
        )

        self.assertEqual(
            vw.to_dict()["data"],
            table.to_table().iloc[0:50, 0:4].to_dict()
        )

        self.assertEqual(
            vw.to_dict(row_page=2, number_of_rows_per_page=3, column_page=2, number_of_columns_per_page=2)["data"],
            table.to_table().iloc[3:6, 2:4].to_dict()
        )
