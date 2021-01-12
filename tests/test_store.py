
import asyncio
import unittest
import os

from gws.settings import Settings
from gws.store import KVStore, FileStore
from gws.file import File

class TestKVStore(unittest.TestCase):

    def test_store(self):
        s1 = KVStore('./store_test/s1')
        s1['city'] = 'Tokyo'
        s1['name'] = 'Elon'

        s2 = KVStore('./store_test/s1')
        self.assertEquals(s2['city'], 'Tokyo')
        self.assertEquals(s2['name'], 'Elon')
        s2['name'] = 'Musk'

        self.assertEquals(s1['name'], 'Musk')

        s2.delete('name')
        self.assertEquals(s2.get('name'), None)
        self.assertEquals(s1.get('name'), None)
    
        s2['name'] = 'Elon'
        
        # connect s2 to another file
        s2 = KVStore('./store_test/s3')
        s2['name'] = 'Lee'
        self.assertEquals(s2['name'], 'Lee')
        self.assertEquals(s1['name'], 'Elon')


class TestFileStore(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        File.drop_table()
        FileStore.remove_all_files(ignore_errors=True)
        pass

    @classmethod
    def tearDownClass(cls):
        #fs._remove_all_files(ignore_errors=True)
        pass
    
    def test_file_store(self):
        fs = FileStore()
        
        settings = Settings.retrieve()
        testdata_dir = settings.get_dir("gws:testdata_dir")
        file_path = os.path.join(testdata_dir, "mini_travel_graph.json")
        
        file = fs.push(file_path)        
        self.assertTrue(file.exists())        

        file = fs.push(file_path)
        self.assertTrue(file.exists())

