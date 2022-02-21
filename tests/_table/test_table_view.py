
from gws_core import BaseTestCase, ViewTester
from gws_core.extra import DataProvider, TableView


class TestTableView(BaseTestCase):

    async def test_table_view(self,):
        table = DataProvider.get_iris_table()

        print(table)

        vw = TableView(table)
        tester = ViewTester(view=vw)
        dic = tester.to_dict(dict(
            from_row=1,
            number_of_rows_per_page=50,
            from_column=1,
            number_of_columns_per_page=50
        ))
        self.assertEqual(dic["type"], "table-view")
        self.assertEqual(
            dic["data"],
            table.to_dataframe().iloc[0:50, 0:5].to_dict('list')
        )
        self.assertEqual(len(dic["row_tags"]), 50)
        self.assertEqual(len(dic["column_tags"]), 5)

        tester = ViewTester(view=vw)
        dic = tester.to_dict(dict(
            from_row=3,
            number_of_rows_per_page=3,
            from_column=2,
            number_of_columns_per_page=2
        ))
        self.assertEqual(
            dic["data"],
            table.to_dataframe().iloc[2:5, 1:3].to_dict('list')
        )
        self.assertEqual(len(dic["row_tags"]), 3)
        self.assertEqual(len(dic["column_tags"]), 2)
