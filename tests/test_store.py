
import asyncio
import unittest
import os

from gws.settings import Settings
from gws.store import KVStore

class TestKVStore(unittest.TestCase):

    def test_store(self):
        settings = Settings.retrieve()
        dir_path = settings.get_data("db_dir")
        file_path = os.path.join(dir_path,'./store_test/s1/')

        s1 = KVStore(file_path)
        s1['city'] = 'Tokyo'
        s1['name'] = 'Elon'

        s2 = KVStore(file_path)
        self.assertEquals(s2['city'], 'Tokyo')
        self.assertEquals(s2['name'], 'Elon')
        s2['name'] = 'Musk'

        self.assertEquals(s1['name'], 'Musk')

        s2.remove('name')
        self.assertEquals(s2['name'], None)
        self.assertEquals(s1['name'], None)


    def test_lazy_store(self):
        settings = Settings.retrieve()
        dir_path = settings.get_data("db_dir")
        file_path = os.path.join(dir_path,'./store_test/s2/')
        s1 = KVStore() 
        s1['city'] = 'Tokyo'
        s1['name'] = 'Elon'
        s1.connect(file_path)

        # connect s2 to s1 file
        s2 = KVStore(file_path)
        self.assertEquals(s2['city'], 'Tokyo')
        self.assertEquals(s2['name'], 'Elon')
        s2['name'] = 'Elon'

        # connect s2 to another file
        file_path2 = os.path.join(dir_path,'./store_test/s3/')
        s2 = KVStore(file_path2)
        s2['name'] = 'Lee'
        self.assertEquals(s2['name'], 'Lee')
        self.assertEquals(s1['name'], 'Elon')



