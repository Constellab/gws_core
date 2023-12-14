# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from unittest import TestCase

from gws_core import ViewTester, ViewType
from gws_core.extra import DataProvider, TableView


# test_table_view
class TestTableView(TestCase):

    def test_table_view(self):
        table = DataProvider.get_iris_table()
        vw = TableView(table)
        tester = ViewTester(view=vw)
        dic = tester.to_dict(dict(
            from_row=1,
            number_of_rows_per_page=50,
            from_column=1,
            number_of_columns_per_page=50
        ))
        self.assertEqual(dic["type"], ViewType.TABLE.value)

        self.assertEqual(
            dic["data"]["table"],
            table.to_dataframe().iloc[0:50, 0:5].to_dict('split')["data"]
        )
        self.assertEqual(len(dic["data"]["rows"]), 50)
        self.assertEqual(len(dic["data"]["columns"]), 5)

        tester = ViewTester(view=vw)
        dic = tester.to_dict(dict(
            from_row=3,
            number_of_rows_per_page=3,
            from_column=2,
            number_of_columns_per_page=2
        ))
        self.assertEqual(
            dic["data"]["table"],
            table.to_dataframe().iloc[2:5, 1:3].to_dict('split')["data"]
        )
        self.assertEqual(len(dic["data"]["rows"]), 3)
        self.assertEqual(len(dic["data"]["columns"]), 2)
