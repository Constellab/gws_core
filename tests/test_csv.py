# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import json
import unittest
import asyncio

import pandas
from pandas import DataFrame

from gws.settings import Settings
from gws.model import Protocol, Study, User
from gws.csv import *
from gws.file import File
from gws.store import LocalFileStore
from gws.unittest import GTest

settings = Settings.retrieve()
testdata_dir = settings.get_dir("gws:testdata_dir")

class TestCSV(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        LocalFileStore.remove_all_files(ignore_errors=True)
        File.drop_table()
        CSVDumper.drop_table()
        CSVLoader.drop_table()
        CSVImporter.drop_table()
        CSVExporter.drop_table()
        Study.drop_table()
        User.drop_table()
        GTest.init()
        pass

    @classmethod
    def tearDownClass(cls):
        LocalFileStore.remove_all_files(ignore_errors=True)
        File.drop_table()
        CSVDumper.drop_table()
        CSVLoader.drop_table()
        CSVImporter.drop_table()
        CSVExporter.drop_table()
        Study.drop_table()
        User.drop_table()
        pass

    
    def test_csv_data(self):
        d = CSVData(table=[ [1, 2, 3] ], column_names=["a","b","c"])
        print(d.table)
        
        d = CSVData(table=[1, 2, 3], column_names=["data"], row_names=["a","b","c"])
        print(d.table)
        
    def test_csv_data_load(self):
        study = Study(data={"title": "Default study", "Description": ""})
        study.save()
        
        file = os.path.join(testdata_dir, "data.csv")
        csv_data = CSVData._import(file)
        
        df = pandas.read_table(file)
        
        print(csv_data.table)
        print(df)
        
        self.assertTrue(df.equals(csv_data.table))
        self.assertEqual(csv_data.column_names, ["A", "B", "C", "D", "E"])
        self.assertEqual(csv_data.row_names, [0, 1])
        
        
    def test_loader_dumper(self):
        i_file_path = os.path.join(testdata_dir, "data.csv")
        o_file_path = os.path.join(testdata_dir, "data_out.csv")
        
        loader = CSVLoader()
        dumper = CSVDumper()
        
        importer = CSVImporter()
        exporter = CSVExporter()
        
        proto = Protocol(
            processes = {
                "loader"   : loader,
                "dumper"   : dumper,
                "exporter" : exporter,
                "importer" : importer,
            },
            connectors = [
                loader>>"data" | dumper<<"data",
                loader>>"data" | exporter<<"data",
                exporter>>"file"   | importer<<"file",
            ]
        )
        
        loader.set_param("file_path", i_file_path)
        dumper.set_param("file_path", o_file_path)
        dumper.set_param("index", False)
        exporter.set_param("index", False)
        
        e = proto.create_experiment(study=GTest.study,user=GTest.user)
        
        def _on_end(*args, **kwargs):
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
        
        
        if os.path.exists(o_file_path):
            os.unlink(o_file_path)
        
        self.assertFalse(os.path.exists(o_file_path))
        
        e.on_end( _on_end )
        asyncio.run( e.run(user=GTest.user) )
