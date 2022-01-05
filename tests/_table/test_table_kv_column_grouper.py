# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import math

from gws_core import BaseTestCase, TableKVColumnGrouper, TaskRunner
from gws_core_test_helper import GWSCoreTestHelper


class TestTableGrouper(BaseTestCase):
    async def test_table_grouper(self):
        table = GWSCoreTestHelper.get_annotated_table()
        print(table)

        # filter columns
        tester = TaskRunner(
            params={
                'grouping_key': "Gender"
            },
            inputs={'table': table},
            task_type=TableKVColumnGrouper,
        )
        outputs = await tester.run()
        data = outputs["table"].get_data()

        self.assertEqual(data.columns.to_list(), ["Gender:F", "Gender:M"])
        self.assertEqual(data.iloc[0, 0], 2.0)
        self.assertEqual(data.iloc[4, 0], 4.0)
        self.assertEqual(data.iloc[7, 0], 10.0)
        self.assertTrue(math.isnan(data.iloc[8, 0]))
        self.assertTrue(math.isnan(data.iloc[15, 0]))

        self.assertEqual(data.iloc[0, 1], 1.0)
        self.assertEqual(data.iloc[4, 1], 3.0)
        self.assertEqual(data.iloc[7, 1], 9.0)
        self.assertTrue(math.isnan(data.iloc[6, 1]))
        self.assertEqual(data.iloc[15, 1], 12.0)

        print(data)
