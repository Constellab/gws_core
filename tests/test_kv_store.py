# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import shelve
import unittest

from gws_core import GTest, KVStore


class TestKVStore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()

    def test_store(self):
        GTest.print("KVStore")

        s1 = KVStore('./store_test/s1')
        s1['city'] = 'Tokyo'
        s1['name'] = 'Elon'
        s2 = KVStore('./store_test/s1')
        self.assertEqual(s2['city'], 'Tokyo')
        self.assertEqual(s2['name'], 'Elon')
        s2['name'] = 'Musk'

        self.assertEqual(s1['name'], 'Musk')

        # test length
        self.assertEqual(len(s1), 2)

        # Test all the iterators
        keys = ['city', 'name']
        values = ['Tokyo', 'Musk']

        index = 0
        for key in s1:
            self.assertEqual(key, keys[index])
            index += 1

        index = 0
        for key in s1.keys():
            self.assertEqual(key, keys[index])
            index += 1

        index = 0
        for value in s1.values():
            self.assertEqual(value, values[index])
            index += 1

        index = 0
        for key, value in s1.items():
            self.assertEqual(key, keys[index])
            self.assertEqual(value, values[index])
            index += 1

        # s2.delete('name')
        del s2["name"]
        self.assertEqual(s2.get('name'), None)
        self.assertEqual(s1.get('name'), None)

        s2['name'] = 'Elon'

        # connect s2 to another file
        s2 = KVStore('./store_test/s3')
        s2['name'] = 'Lee'
        self.assertEqual(s2['name'], 'Lee')
        self.assertEqual(s1['name'], 'Elon')
