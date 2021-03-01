
import asyncio
import unittest
import os

from gws.settings import Settings
from gws.store import KVStore, LocalFileStore, RemoteFileStore
from gws.file import File

# OVHRemoteFileStore class
class OVHRemoteFileStore(RemoteFileStore):
    _default_container_url = "https://storage.sbg.cloud.ovh.net/v1/AUTH_a0286631d7b24afba3f3cdebed2992aa/public_test"
    pass

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


class TestLocalFileStore(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        File.drop_table()
        LocalFileStore.remove_all_files(ignore_errors=True)
        pass

    @classmethod
    def tearDownClass(cls):
        #fs._remove_all_files(ignore_errors=True)
        pass
    
    def test_file_store(self):
        fs = LocalFileStore()
        
        settings = Settings.retrieve()
        testdata_dir = settings.get_dir("gws:testdata_dir")
        file_path = os.path.join(testdata_dir, "mini_travel_graph.json")
        
        file = fs.add(file_path)        
        self.assertTrue(file.exists())        

        file = fs.add(file_path)
        self.assertTrue(file.exists())
        self.assertTrue(fs.contains(file))
        
        file2= File()
        file2.path = file_path
        print(file2.path)
        
        self.assertFalse(fs.contains(file2))
        file2.move_to_store(fs)
        self.assertTrue(fs.contains(file2))
        print(file2.path)

class TestRemoteFileStore(unittest.TestCase):
    
    def test_file_store(self):
        return
        settings = Settings.retrieve()
        testdata_dir = settings.get_dir("gws:testdata_dir")
        file_path = os.path.join(testdata_dir, "mini_travel_graph.json")
        fs = OVHRemoteFileStore(path = "https://storage.sbg.cloud.ovh.net/v1/AUTH_a0286631d7b24afba3f3cdebed2992aa/public_test")
        f = fs.add(file_path)
        print(f.path)

