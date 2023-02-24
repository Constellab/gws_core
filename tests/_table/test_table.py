# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from unittest import IsolatedAsyncioTestCase

from pandas import DataFrame

from gws_core import Table
from gws_core.core.utils.utils import Utils


# test_table
class TestTable(IsolatedAsyncioTestCase):
    def test_table(self):
        table: Table = Table(data=[[1, 2, 3]], column_names=["a", "b", "c"], row_names=["r0"])

        expected_df = DataFrame({'a': [1], 'b': [2], 'c': [3]}, index=["r0"])
        self.assertTrue(table.get_data().equals(expected_df))
        self.assertEqual(table.column_names, ["a", "b", "c"])
        self.assertEqual(table.row_names, ["r0"])
        Utils.assert_json_equals(table.get_row_tags(), [{}])
        Utils.assert_json_equals(table.get_column_tags(), [{}, {}, {}])
        self.assertEqual(table.comments, None)

    def test_create_sub_table(self):
        dataframe = DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})

        row_tags = [{'a': "1"}, {'a': "2"}, {'a': "3"}]
        column_tags = [{'b': "4"}, {'b': "5"}]

        table = Table(data=dataframe, row_tags=row_tags, column_tags=column_tags)

        # Simulate the filter by column B
        sub_dataframe = DataFrame({'A': [1, 2, 3]})

        sub_table = table.create_sub_table_filtered_by_columns(sub_dataframe)
        self.assertTrue(sub_table.get_data().equals(sub_dataframe.copy()))
        self.assertEqual(sub_table.get_row_tags(), row_tags)
        # there should be only one column --> one tag
        self.assertEqual(sub_table.get_column_tags(), [{'b': "4"}])

        # Simulate the filter by row 1 & 2
        sub_dataframe = DataFrame({'A': [1, 2], 'B': [4, 5]}, index=['0', '1'])

        sub_table = table.create_sub_table_filtered_by_rows(sub_dataframe)
        self.assertTrue(sub_table.get_data().equals(sub_dataframe.copy()))
        self.assertEqual(sub_table.get_column_tags(), column_tags)
        # there should be only two rows --> two tag
        self.assertEqual(sub_table.get_row_tags(), [{'a': "1"}, {'a': "2"}])

    def test_table_select(self):
        row_tags = [
            {"lg": "EN", "c": "US", "user": "Vi"},
            {"lg": "JP", "c": "JP", "user": "Jo"},
            {"lg": "FR", "c": "FR", "user": "Jo"},
        ]
        column_tags = [
            {"lg": "EN", "c": "UK"},
            {"lg": "PT", "c": "PT"},
            {"lg": "CH", "c": "CH"}
        ]

        table: Table = Table(
            data=[[1, 2, 3], [3, 4, 6], [3, 7, 6]],
            row_names=["NY", "Tokyo", "Paris"],
            column_names=["London", "Lisboa", "Beijin"],
            row_tags=row_tags,
            column_tags=column_tags
        )

        # ------------------------------------------------------------
        # Select by row positions
        # ------------------------------------------------------------

        sub_table = table.select_by_row_positions([1, 2])
        self.assertEqual(sub_table.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(sub_table.row_names, ["Tokyo", "Paris"])
        self.assertEqual(sub_table.get_row_tags(), [
            {"lg": "JP", "c": "JP", "user": "Jo"},
            {"lg": "FR", "c": "FR", "user": "Jo"},
        ])
        self.assertEqual(sub_table.get_column_tags(), [
            {"lg": "EN", "c": "UK"},
            {"lg": "PT", "c": "PT"},
            {"lg": "CH", "c": "CH"}
        ])

        sub_table = table.select_by_row_positions([1, 2, 1])
        self.assertEqual(sub_table.row_names, ["Tokyo", "Paris", "Tokyo_1"])

        # ------------------------------------------------------------
        # Select by column positions
        # ------------------------------------------------------------

        sub_table = table.select_by_column_positions([0, 2])
        self.assertEqual(sub_table.column_names, ["London", "Beijin"])
        self.assertEqual(sub_table.row_names, ["NY", "Tokyo", "Paris"])
        self.assertEqual(sub_table.get_row_tags(), [
            {"lg": "EN", "c": "US", "user": "Vi"},
            {"lg": "JP", "c": "JP", "user": "Jo"},
            {"lg": "FR", "c": "FR", "user": "Jo"},
        ])
        self.assertEqual(sub_table.get_column_tags(), [
            {"lg": "EN", "c": "UK"},
            {"lg": "CH", "c": "CH"}
        ])

        # check that is we are selecting a column twice, it return the column twice
        sub_table = table.select_by_column_positions([0, 2, 0])
        self.assertEqual(sub_table.column_names, ["London", "Beijin", "London_1"])

        # ------------------------------------------------------------
        # Select by row names
        # ------------------------------------------------------------

        sub_table = table.select_by_row_names([{"name": ["Toky.*"], "is_regex": True}])
        self.assertEqual(sub_table.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(sub_table.row_names, ["Tokyo"])
        self.assertEqual(sub_table.get_row_tags(), [
            {"lg": "JP", "c": "JP", "user": "Jo"},
        ])
        self.assertEqual(sub_table.get_column_tags(), [
            {"lg": "EN", "c": "UK"},
            {"lg": "PT", "c": "PT"},
            {"lg": "CH", "c": "CH"}
        ])

        # ------------------------------------------------------------
        # Select by column names
        # ------------------------------------------------------------

        sub_table = table.select_by_column_names([{"name": ["L.*"], "is_regex": True}])
        self.assertEqual(sub_table.column_names, ["London", "Lisboa"])
        self.assertEqual(sub_table.row_names, ["NY", "Tokyo", "Paris"])
        self.assertEqual(sub_table.get_row_tags(), [
            {"lg": "EN", "c": "US", "user": "Vi"},
            {"lg": "JP", "c": "JP", "user": "Jo"},
            {"lg": "FR", "c": "FR", "user": "Jo"},
        ])
        self.assertEqual(sub_table.get_column_tags(), [
            {"lg": "EN", "c": "UK"},
            {"lg": "PT", "c": "PT"},
        ])

        sub_table = table.select_by_column_names([{"name": ["L.*", "B.*"], "is_regex": True}])
        self.assertEqual(sub_table.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(sub_table.row_names, ["NY", "Tokyo", "Paris"])

        sub_table = table.select_by_row_names([{"name": ["Tokyo", "Oui"]}])
        self.assertEqual(sub_table.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(sub_table.row_names, ["Tokyo"])

        # ------------------------------------------------------------
        # Select by column tags
        # ------------------------------------------------------------

        sub_table = table.select_by_column_tags([{"lg": "PT"}])
        self.assertEqual(sub_table.column_names, ["Lisboa"])
        self.assertEqual(sub_table.row_names, ["NY", "Tokyo", "Paris"])

        sub_table = table.select_by_column_tags([{"lg": "PT", "c": "PT"}])
        self.assertEqual(sub_table.column_names, ["Lisboa"])
        self.assertEqual(sub_table.row_names, ["NY", "Tokyo", "Paris"])

        # ------------------------------------------------------------
        # Select by row tags
        # ------------------------------------------------------------

        # ( t1 )
        sub_table = table.select_by_row_tags([{"c": "JP"}])
        self.assertEqual(sub_table.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(sub_table.row_names, ["Tokyo"])

        # ( t2 )
        sub_table = table.select_by_row_tags([{"user": "Jo"}])
        self.assertEqual(sub_table.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(sub_table.row_names, ["Tokyo", "Paris"])

        # ( t1 AND t2 )
        sub_table = table.select_by_row_tags([{"c": "JP", "user": "Jo"}])
        self.assertEqual(sub_table.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(sub_table.row_names, ["Tokyo"])

        # ( t1 ) OR ( t2 )
        sub_table = table.select_by_row_tags([{"user": "Jo"}, {"c": "JP"}])
        self.assertEqual(sub_table.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(sub_table.row_names, ["Tokyo", "Paris"])

        # ( t1 AND t2 ) OR t2
        sub_table = table.select_by_row_tags([{"user": "Jo", "c": "JP"}, {"c": "JP"}])
        self.assertEqual(sub_table.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(sub_table.row_names, ["Tokyo"])

        # ( t1 AND t2 ) OR t1
        sub_table = table.select_by_row_tags([{"user": "Jo", "c": "JP"}, {"user": "Jo"}])
        self.assertEqual(sub_table.column_names, ["London", "Lisboa", "Beijin"])
        self.assertEqual(sub_table.row_names, ["Tokyo", "Paris"])

    def test_generate_column_name(self):
        dataframe = DataFrame({'A': range(1, 6)})

        table = Table(data=dataframe)
        self.assertEqual(table.generate_new_column_name('Test'), 'Test')
        # test generating a new that already exists
        self.assertEqual(table.generate_new_column_name('A'), 'A_1')

    def test_equals(self):
        first: Table = Table(DataFrame({'A': [1, 2, 3]}), row_names=['r0', 'r1', 'r2'],
                             row_tags=[{'lg': 'EN'}, {'lg': 'FR'}, {'lg': 'EN'}], column_tags=[{'c': 'UK'}])
        second: Table = Table(DataFrame({'A': [1, 2, 3]}), row_names=['r0', 'r1', 'r2'],
                              row_tags=[{'lg': 'EN'}, {'lg': 'FR'}, {'lg': 'EN'}], column_tags=[{'c': 'UK'}])

        self.assertTrue(first.equals(second))

        # wrong dataframe
        second = Table(DataFrame({'B': [1, 2, 3]}), row_names=['r0', 'r1', 'r2'],
                       row_tags=[{'lg': 'EN'}, {'lg': 'FR'}, {'lg': 'EN'}], column_tags=[{'c': 'UK'}])
        self.assertFalse(first.equals(second))

        # wrong row tags
        second = Table(DataFrame({'A': [1, 2, 3]}), row_names=['r0', 'r1', 'r2'],
                       row_tags=[{'lg': 'EN'}, {'lg': 'EN'}, {'lg': 'EN'}], column_tags=[{'c': 'UK'}])
        self.assertFalse(first.equals(second))

        # wrong column tags
        second = Table(DataFrame({'A': [1, 2, 3]}), row_names=['r0', 'r1', 'r2'],
                       row_tags=[{'lg': 'EN'}, {'lg': 'FR'}, {'lg': 'EN'}], column_tags=[{'c': 'FR'}])

        self.assertFalse(first.equals(second))

    def test_column_table_modification(self):
        table = Table()

        # test adding and empty column to an empty table
        table.add_column('A')
        expected_table = Table(DataFrame({'A': [None]}))
        self.assertTrue(table.equals(expected_table))

        # test adding and removing a column
        table = Table()
        table.add_column('A', [1, 2, 3])

        expected_table = Table(DataFrame({'A': [1, 2, 3]}))
        self.assertTrue(table.equals(expected_table))

        # adding an empty column
        table.add_column('B')
        expected_table = Table(DataFrame({'A': [1, 2, 3], 'B': [None, None, None]}))
        self.assertTrue(table.equals(expected_table))

        # removing B column
        table.remove_column('B')
        expected_table = Table(DataFrame({'A': [1, 2, 3]}))
        self.assertTrue(table.equals(expected_table))

    def test_row_table_modification(self):
        table = Table()

        # test adding and empty row to an empty table
        table.add_row('A')
        expected_table = Table(DataFrame({'0': [None]}), row_names=['A'])
        self.assertTrue(table.equals(expected_table))

        # test adding and removing a row
        table = Table()
        table.add_row('A', [1, 2, 3])

        expected_table = Table(DataFrame({'0': [1], '1': [2], '2': [3]}), row_names=['A'])
        self.assertTrue(table.equals(expected_table))

        # adding an empty row
        table.add_row('B')
        self.assertEqual(table.row_names, ['A', 'B'])
        self.assertEqual(table.get_row_data('B'), [None, None, None])

        # removing B row
        table.remove_row('B')
        # table.convert_dtypes()
        self.assertEqual(table.row_names, ['A'])

    def test_set_cell_value(self):
        table = Table(DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]}))
        self.assertEqual(table.get_cell_value_at(0, 1), 4)

        table.set_cell_value_at(0, 1, 7)
        self.assertEqual(table.get_cell_value_at(0, 1), 7)

    def test_set_row_name(self):
        table = Table(DataFrame({'A': [1, 2], 'B': [4, 5]}))

        table.set_row_name('0', 'r0')
        self.assertEqual(table.row_names[0], 'r0')

        table.set_all_row_names(['r1', 'r2'])
        self.assertEqual(table.row_names, ['r1', 'r2'])

    def test_set_column_name(self):
        table = Table(DataFrame({'A': [1, 2], 'B': [4, 5]}))

        table.set_column_name('A', 'C')
        self.assertEqual(table.column_names[0], 'C')

        table.set_all_column_names(['D', 'E'])
        self.assertEqual(table.column_names, ['D', 'E'])

    def test_table_column_row_names(self):
        # Test duplicate name and name with special characters
        table = Table(DataFrame({'0': [1, 2], '1': [4, 5], '2': [4, 5]}),
                      row_names=['r0', 'r0'],
                      column_names=['A', 'A', 1])

        self.assertEqual(table.row_names, ['r0', 'r0_1'])
        self.assertEqual(table.column_names, ['A', 'A_1', '1'])
