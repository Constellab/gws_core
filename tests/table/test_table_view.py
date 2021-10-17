import os

from gws_core import BaseTestCase, Settings, Table, TableView


class TestTableView(BaseTestCase):

    def test_table_view(self,):
        settings = Settings.retrieve()
        testdata_dir = settings.get_variable("gws_core:testdata_dir")
        file_path = os.path.join(testdata_dir, "iris.csv")
        table = Table.import_from_path(file_path, delimiter=",", head=0)
        vw = TableView(table)

        self.assertEqual(
            vw._slice_data(from_row_index=4, to_row_index=21, from_column_index=1, to_column_index=4),
            table.to_table().iloc[4:21, 1:4].to_dict('list')
        )
        
        print(table)
        dic = vw.to_dict()
        self.assertEqual(dic["type"], "table-view")
        self.assertEqual(
            dic["data"],
            table.to_table().iloc[0:50, 0:5].to_dict('list')
        )

        self.assertEqual(
            vw.to_dict(from_row=3, number_of_rows_per_page=3, from_column=2, number_of_columns_per_page=2)["data"],
            table.to_table().iloc[2:5, 1:3].to_dict('list')
        )