# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

import pandas
from gws_core import (CSVDumper, CSVExporter, CSVImporter, CSVLoader, CSVTable,
                      Experiment, ExperimentService, File, GTest,
                      ProcessableFactory, ProcessModel, ProtocolModel,
                      ProtocolService, Settings, Study)

from tests.base_test import BaseTest

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestCSV(BaseTest):

    def test_csv_data(self):
        GTest.print("CSVData")

        csv_table: CSVTable = CSVTable()
        csv_table.set_data(table=[[1, 2, 3]], column_names=["a", "b", "c"])
        print(csv_table.table)

        csv_table.set_data(table=[1, 2, 3], column_names=[
            "data"], row_names=["a", "b", "c"])
        print(csv_table.table)

    def test_csv_data_load(self):
        GTest.print("CSVData load")

        study = Study(data={"title": "Default study", "Description": ""})
        study.save()

        file = os.path.join(testdata_dir, "data.csv")
        csv_data = CSVTable.import_resource(file)

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

        loader: ProcessModel = ProcessableFactory.create_process_model_from_type(
            CSVLoader)
        dumper: ProcessModel = ProcessableFactory.create_process_model_from_type(
            CSVDumper)

        importer: ProcessModel = ProcessableFactory.create_process_model_from_type(
            CSVImporter)
        exporter: ProcessModel = ProcessableFactory.create_process_model_from_type(
            CSVExporter)

        proto: ProtocolModel = ProtocolService.create_protocol_from_data(
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

        # refresh the processes
        importer = experiment.protocol.get_process("importer")
        loader = experiment.protocol.get_process("loader")
        dumper = experiment.protocol.get_process("dumper")
        exporter = experiment.protocol.get_process("exporter")
        csv_data: CSVTable = loader.output["data"].get_resource()

        i_df = pandas.read_table(i_file_path)
        o_df = pandas.read_table(o_file_path)

        self.assertTrue(i_df.equals(csv_data.table))
        self.assertTrue(i_df.equals(o_df))

        if os.path.exists(o_file_path):
            os.unlink(o_file_path)
        self.assertFalse(os.path.exists(o_file_path))

        file: File = exporter.output["file"]
        self.assertTrue(os.path.exists(file.path))

        o_csv_data: CSVTable = importer.output["data"].get_resource()
        self.assertTrue(csv_data.table.equals(o_csv_data.table))
