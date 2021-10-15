# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

import pandas
from gws_core import (BaseTestCase, ConfigParams, TableDumper, TableExporter,
                      TableImporter, TableLoader, Table, Experiment,
                      ExperimentService, File, GTest, Protocol, ProtocolModel,
                      ProtocolService, Settings, TaskModel, protocol_decorator)
from gws_core.protocol.protocol_spec import ProcessSpec

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")

i_file_path = os.path.join(testdata_dir, "data.csv")
o_file_path = os.path.join(testdata_dir, "data_out.csv")


@protocol_decorator("TableProtocol")
class TableProtocol(Protocol):
    def configure_protocol(self, config_params: ConfigParams) -> None:

        loader: ProcessSpec = self.add_process(
            TableLoader, 'loader').set_param(
            "file_path", i_file_path)
        dumper: ProcessSpec = self.add_process(TableDumper, 'dumper')\
            .set_param("file_path", o_file_path).set_param("index", False)

        importer: ProcessSpec = self.add_process(TableImporter, 'importer')
        exporter: ProcessSpec = self.add_process(TableExporter, 'exporter').set_param("index", False)

        self.add_connectors([
            (loader >> "data", dumper << "data"),
            (loader >> "data", exporter << "data"),
            (exporter >> "file", importer << "file"),
        ])


class TestTable(BaseTestCase):

    def test_table(self):
        GTest.print("Table")

        table: Table = Table()
        table.set_data(data=[[1, 2, 3]], column_names=["a", "b", "c"])
        print(table.get_data())

        table.set_data(data=[1, 2, 3], column_names=[
            "data"], row_names=["a", "b", "c"])
        print(table.get_data())

    def test_table_load(self):
        GTest.print("Table load")

        file = os.path.join(testdata_dir, "data.csv")
        table = Table.import_from_path(file)

        df = pandas.read_table(file)

        print(df)

        self.assertTrue(df.equals(table.get_data()))
        self.assertEqual(table.column_names, ["A", "B", "C", "D", "E"])
        self.assertEqual(table.row_names, [0, 1])

    async def test_loader_dumper(self):
        GTest.print("Table Loader and Dumper")

        proto: ProtocolModel = ProtocolService.create_protocol_model_from_type(TableProtocol)

        experiment: Experiment = ExperimentService.create_experiment_from_protocol_model(
            protocol_model=proto)

        if os.path.exists(o_file_path):
            os.unlink(o_file_path)

        self.assertFalse(os.path.exists(o_file_path))

        experiment = await ExperimentService.run_experiment(
            experiment=experiment, user=GTest.user)

        print("Test Table import/export")

        importer: TaskModel = experiment.protocol_model.get_process("importer")
        loader: TaskModel = experiment.protocol_model.get_process("loader")
        exporter: TaskModel = experiment.protocol_model.get_process("exporter")
        table: Table = loader.outputs.get_resource_model("data").get_resource()

        i_df = pandas.read_table(i_file_path)
        o_df = pandas.read_table(o_file_path)

        self.assertTrue(i_df.equals(table.get_data()))
        self.assertTrue(i_df.equals(o_df))

        if os.path.exists(o_file_path):
            os.unlink(o_file_path)
        self.assertFalse(os.path.exists(o_file_path))

        file: File = exporter.outputs.get_resource_model("file")
        self.assertTrue(os.path.exists(file.path))

        o_table: Table = importer.outputs.get_resource_model("data").get_resource()
        self.assertTrue(table.get_data().equals(o_table.get_data()))
