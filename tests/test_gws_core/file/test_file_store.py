import os
from unittest import TestCase

from gws_core import File
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.file_store import FileStore
from gws_core.impl.file.local_file_store import LocalFileStore


# test_file_store
class TestLocalFileStore(TestCase):
    def test_file(self):
        file_store: FileStore = LocalFileStore()

        temp_dir = Settings.make_temp_dir()
        tmp_path = str(
            FileHelper.create_empty_file_if_not_exist(os.path.join(temp_dir, "test_file.txt"))
        )

        # Add a file from a path
        file: File = file_store.add_file_from_path(tmp_path)
        self.assertTrue(file_store.node_name_exists(file.get_default_name()))
        self.assertTrue(file_store.node_exists(file))
        self.assertTrue(file_store.node_path_exists(file.path))
        self.assertTrue(file.get_default_name(), "test_file.txt")
        # check that the file was moved
        self.assertTrue(FileHelper.exists_on_os(file.path))
        self.assertFalse(FileHelper.exists_on_os(tmp_path))

        # Try to add a node that is already in the store
        with self.assertRaises(Exception):
            file_store.add_file_from_path(file.path)

        # Add a file with the same name
        tmp_path_2 = str(
            FileHelper.create_empty_file_if_not_exist(os.path.join(temp_dir, "test_file.txt"))
        )

        file_2 = file_store.add_file_from_path(tmp_path_2, "test_file.txt")
        self.assertTrue(file_store.node_exists(file_2))
        self.assertEqual(file_2.get_default_name(), "test_file_1.txt")

        file_store.delete_node(file)
        self.assertFalse(file_store.node_exists(file))

    def test_sanitizer(self):
        self.assertEqual(FileHelper.sanitize_name("\"Az02'{([$*!%?-_/.txt"), "Az02-_/.txt")

        # Test path traversal prevention
        self.assertEqual(FileHelper.sanitize_name("../../../etc/passwd"), "etc/passwd")

        # Test null byte and control character removal
        self.assertEqual(FileHelper.sanitize_name("file\x00name\x01.txt"), "filename.txt")

        # Test empty/dangerous inputs
        self.assertEqual(FileHelper.sanitize_name(".."), "sanitized_file")
        self.assertEqual(FileHelper.sanitize_name(""), "")

        # same names without the ending /
        dangerous_file_name = "\"Az02'{([$*!%?-_.txt"
        safe_file_name = "Az02-_.txt"
        file_store: FileStore = LocalFileStore()

        temp_dir = Settings.make_temp_dir()
        tmp_path = str(
            FileHelper.create_empty_file_if_not_exist(os.path.join(temp_dir, "test_file.txt"))
        )
        # Add a file from a path
        file: File = file_store.add_file_from_path(tmp_path, dangerous_file_name)

        self.assertEqual(file.get_default_name(), safe_file_name)
