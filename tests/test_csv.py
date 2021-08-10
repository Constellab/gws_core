# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from unittest import IsolatedAsyncioTestCase

import pandas
from gws_core import (CSVDumper, CSVExporter, CSVImporter, CSVLoader, CSVTable,
                      Experiment, ExperimentService, GTest, Protocol, Settings,
                      Study)

settings = Settings.retrieve()
testdata_dir = settings.get_dir("gws:testdata_dir")


class TestCSV(IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()

    def test_csv_data(self):
        GTest.print("CSVData")

        d = CSVTable(table=[[1, 2, 3]], column_names=["a", "b", "c"])
        print(d.table)

        d = CSVTable(table=[1, 2, 3], column_names=[
                     "data"], row_names=["a", "b", "c"])
        print(d.table)

    def test_csv_data_load(self):
        GTest.print("CSVData load")

        study = Study(data={"title": "Default study", "Description": ""})
        study.save()

        file = os.path.join(testdata_dir, "data.csv")
        csv_data = CSVTable._import(file)

        df = pandas.read_table(file)

        print(csv_data.table)
        print(df)

        self.assertTrue(df.equals(csv_data.table))
        self.assertEqual(csv_data.column_names, ["A", "B", "C", "D", "E"])
        self.assertEqual(csv_data.row_names, [0, 1])

    async def test_loader_dumper(self):
        GTest.print("CSVData Loader and Dumper")

        i_file_path = os.path.join(testdata_dir, "data.csv")
        o_file_path = os.path.join(testdata_dir, "data_out.csv")

        loader = CSVLoader()
        dumper = CSVDumper()

        importer = CSVImporter()
        exporter = CSVExporter()

        proto = Protocol(
            processes={
                "loader": loader,
                "dumper": dumper,
                "exporter": exporter,
                "importer": importer,
            },
            connectors=[
                loader >> "data" | dumper << "data",
                loader >> "data" | exporter << "data",
                exporter >> "file" | importer << "file",
            ]
        )

        loader.set_param("file_path", i_file_path)
        dumper.set_param("file_path", o_file_path)
        dumper.set_param("index", False)
        exporter.set_param("index", False)

        experiment: Experiment = ExperimentService.create_experiment_from_protocol(
            protocol=proto)

        if os.path.exists(o_file_path):
            os.unlink(o_file_path)

        self.assertFalse(os.path.exists(o_file_path))

        experiment = await ExperimentService.run_experiment(
            experiment=experiment, user=GTest.user)

        print("Test CSV import/export")

        csv_data = loader.output["data"]

        i_df = pandas.read_table(i_file_path)
        o_df = pandas.read_table(o_file_path)

        self.assertTrue(i_df.equals(csv_data.table))
        self.assertTrue(i_df.equals(o_df))

        if os.path.exists(o_file_path):
            os.unlink(o_file_path)
        self.assertFalse(os.path.exists(o_file_path))

        file = exporter.output["file"]
        self.assertTrue(os.path.exists(file.path))

        o_csv_data = importer.output["data"]
        self.assertTrue(csv_data.table.equals(o_csv_data.table))
