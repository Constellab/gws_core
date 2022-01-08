
from gws_core import BaseTestCase, TableView, ViewTester
from gws_core.extra import DataProvider


class TestTableView(BaseTestCase):

    async def test_table_view(self,):
        table = DataProvider.get_iris_table()

        print(table)

        vw = TableView(table)
        self.assertEqual(
            vw._slice(
                vw.get_table().get_data(),
                from_row_index=4, to_row_index=21, from_column_index=1, to_column_index=4),
            table.to_dataframe().iloc[4: 21, 1: 4].to_dict('list'))

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
