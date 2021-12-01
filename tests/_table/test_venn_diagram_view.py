import os

from gws_core import (BaseTestCase, ConfigParams, File, Settings, Table,
                      VennDiagramView, ViewTester)
from gws_core.config.config_types import ConfigParams
from gws_core.impl.file.file import File


class TestVennDiagrammView(BaseTestCase):

    def test_barplot_2d_view(self,):
        settings = Settings.retrieve()
        testdata_dir = settings.get_variable("gws_core:testdata_dir")
        file_path = os.path.join(testdata_dir, "venn_data.csv")
        table = Table.import_from_path(
            File(path=file_path),
            ConfigParams({
                "delimiter": "\t",
                "header": 0
            })
        )
        tester = ViewTester(
            view=VennDiagramView(table)
        )
        dic = tester.to_dict({})

        self.assertEqual(dic["data"]["total_number_of_columns"], 3)
        self.assertEqual(len(dic["data"]["sections"]), 7)
        self.assertEqual(dic["data"]["sections"][6], {'columns': ['A', 'B', 'C'], 'section': {'3', '1'}})

        dic = tester.to_dict({"column_names": ["A", "B"]})
        self.assertEqual(dic["data"]["total_number_of_columns"], 2)
        self.assertEqual(len(dic["data"]["sections"]), 3)

        dic = tester.to_dict({"column_names": ["A", "B", "D", "E"]})
        self.assertEqual(len(dic["data"]["sections"]), 15)
