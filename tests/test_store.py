
import asyncio
import unittest
import os

from gws.settings import Settings
from gws.store import KVStore
from gws.store import FileStore

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
        self.assertEquals(s2['name'], None)
        self.assertEquals(s1['name'], None)
        s2['name'] = 'Elon'
        
        # connect s2 to another file
        s2 = KVStore('./store_test/s3')
        s2['name'] = 'Lee'
        self.assertEquals(s2['name'], 'Lee')
        self.assertEquals(s1['name'], 'Elon')


        
settings = Settings.retrieve()
dir_path = settings.get_data("db_dir")
file_store_path = os.path.join(dir_path,'./file_test/s1')
fs = FileStore(file_store_path)

class TestFileStore(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        fs._remove_all_files(ignore_errors=True)
        pass

    @classmethod
    def tearDownClass(cls):
        #fs._remove_all_files(ignore_errors=True)
        pass
    
    def test_file_store(self):
        testdata_dir = settings.get_dir("gws:testdata_dir")
        file_path = os.path.join(testdata_dir, "protocol_graph.json")
        rel_file_path = fs.push(file_path)
        
        self.assertTrue(fs.exists(rel_file_path))        
        self.assertRaises(Exception, fs.push, file_path)

        rel_file_path = fs.push(file_path, slot="./new_dir")
        self.assertTrue(fs.exists(rel_file_path))
        
        rel_file_path = fs.push(file_path, slot="./new_dir", force=True)
        self.assertTrue(fs.exists(rel_file_path))
        
        
        fs.move(rel_file_path, "/oui/non/rien/ce-fichier.json")
        self.assertFalse(fs.exists(rel_file_path))
        self.assertTrue(fs.exists("/oui/non/rien/ce-fichier.json"))
        
        
        fs.move("/oui/non/rien/ce-fichier.json", "/paris/eiffel.json")
        self.assertFalse(fs.exists("/oui/non/rien/ce-fichier.json"))
        self.assertTrue(fs.exists("/paris/eiffel.json"))
        
    
    def test_file_upload(self):
        testdata_dir = settings.get_dir("gws:testdata_dir")
        file_path = os.path.join(testdata_dir, "protocol_graph.json")
        
        with open(file_path, "rb") as fp:
            fs.push(fp, dest_file_name="leon.json", slot="uploads")
            self.assertTrue(fs.exists("/uploads/leon.json"))

