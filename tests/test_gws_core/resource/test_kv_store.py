import os
import pickle
from unittest import TestCase, skipUnless

from gws_core import KVStore
from gws_core.impl.file.file_helper import FileHelper

try:
    from dbm import ndbm
except ImportError:
    ndbm = None


# test_kv_store
class TestKVStore(TestCase):
    def test_empty(self):
        s1 = KVStore.empty()
        s1["test"] = "Super"
        self.assertEqual(s1["test"], "Super")
        self.assertTrue(s1.file_exists())

        s1.remove()
        self.assertFalse(s1.file_exists())
        self.assertFalse(FileHelper.exists_on_os(s1.full_file_dir))

    def test_store(self):
        s1 = KVStore.from_filename("s1")

        # Test that the file is not created on kv store creation
        self.assertFalse(FileHelper.exists_on_os(KVStore.get_full_file_path("s1")))

        s1["city"] = "Tokyo"
        s1["name"] = "Elon"
        s2 = KVStore.from_filename("s1")
        self.assertEqual(s2["city"], "Tokyo")
        self.assertEqual(s2["name"], "Elon")
        s2["name"] = "Musk"

        self.assertEqual(s1["name"], "Musk")

        # test length
        self.assertEqual(len(s1), 2)

        # Test all the iterators
        keys = ["city", "name"]
        values = ["Tokyo", "Musk"]

        for index, key in enumerate(s1):
            self.assertEqual(key, keys[index])

        index = 0
        for key in s1.keys():  # noqa: SIM118 - the test exercises the .keys() API itself
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
        self.assertEqual(s2.get("name"), None)
        self.assertEqual(s1.get("name"), None)

        s2["name"] = "Elon"

        # connect s2 to another file
        s2 = KVStore.from_filename("s3")
        s2["name"] = "Lee"
        self.assertEqual(s2["name"], "Lee")
        self.assertEqual(s1["name"], "Elon")

    def test_lock(self):
        test_lock = KVStore.from_filename("test_lock")
        test_lock["city"] = "Tokyo"
        test_lock["name"] = "Elon"

        test_lock.lock("test_lock_2")

        self.assertEqual(test_lock["city"], "Tokyo")
        # Test that the read did not create a copy of the file
        self.assertFalse(FileHelper.exists_on_os(KVStore.get_full_file_path("test_lock_2")))

        # Update the kvstore, it should create a new file
        test_lock["city"] = "London"
        # check that the file was created
        self.assertTrue(FileHelper.exists_on_os(KVStore.get_full_file_path("test_lock_2")))
        self.assertEqual(test_lock["city"], "London")

        # Check that the first store was not updated
        first_store = KVStore.from_filename("test_lock")
        self.assertEqual(first_store["city"], "Tokyo")

    @skipUnless(ndbm is not None, "the dbm.ndbm backend is not available on this system")
    def test_legacy_store(self):
        """Check that a store written by the dbm.ndbm backend (the default one before
        Python 3.13, so the one that wrote the stores of the existing labs) is still
        found and read, whatever the backend shelve now defaults to."""
        kv_store = KVStore.from_filename("test_legacy_store")
        os.makedirs(kv_store.full_file_dir, exist_ok=True)

        legacy_store = ndbm.open(kv_store.get_full_path_without_extension(), "c")
        legacy_store["city"] = pickle.dumps("Tokyo")
        legacy_store.close()

        # the ndbm backend appends '.db' to the store path
        self.assertEqual(kv_store.full_file_path, kv_store.get_full_path_without_extension() + ".db")
        self.assertTrue(kv_store.file_exists())
        self.assertEqual(kv_store["city"], "Tokyo")

        # and it can still be written to
        kv_store["city"] = "London"
        self.assertEqual(kv_store["city"], "London")

    def test_generate_new_file(self):
        kv_store = KVStore.from_filename("test_generate_new_file")

        path = kv_store.generate_new_file()
        FileHelper.exists_on_os(path)
