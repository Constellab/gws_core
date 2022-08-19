# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import BaseTestCase, File, LocalFileStore
from gws_core.data_provider.data_provider import DataProvider
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.file_store import FileStore
from gws_core.impl.file.folder import Folder


# test_file_store
class TestLocalFileStore(BaseTestCase):

    def test_file(self):
        file_store: FileStore = LocalFileStore()

        file_path = DataProvider.get_test_data_path("mini_travel_graph.json")

        # Add a file from a path
        file: File = file_store.add_file_from_path(file_path)
        self.assertTrue(file_store.node_name_exists(file.get_default_name()))
        self.assertTrue(file.get_default_name(), 'mini_travel_graph.json')

        # Add a file with the same name
        file_2 = file_store.add_file_from_path(file_path, 'mini_travel_graph.json')
        self.assertTrue(file_store.node_exists(file_2))
        self.assertEqual(file_2.get_default_name(), 'mini_travel_graph_1.json')

        file_store.delete_node(file)
        self.assertFalse(file_store.node_exists(file))

    def test_empty_file(self):
        file_store: FileStore = LocalFileStore()

        # Create an empty file
        empty_file: File = file_store.create_empty_file('test_file.txt')
        self.assertTrue(file_store.node_exists(empty_file))
        self.assertTrue(FileHelper.exists_on_os(empty_file.path))

    def test_empty_folder(self):
        file_store: FileStore = LocalFileStore()

        # Create an empty folder
        folder: Folder = file_store.create_empty_folder('my-folder')
        self.assertTrue(file_store.node_exists(folder))
        self.assertTrue(FileHelper.exists_on_os(folder.path))
        self.assertEqual(folder.get_default_name(), 'my-folder')

        # Create a folder with the same name
        folder: Folder = file_store.create_empty_folder('my-folder')
        self.assertEqual(folder.get_default_name(), 'my-folder_1')
        self.assertTrue(FileHelper.exists_on_os(folder.path))

        file_store.delete_node(folder)
        self.assertFalse(file_store.node_exists(folder))

    def test_sanitizer(self):

        dangerous_file_name = "\"Az02'{([$*!%?-_/.txt"
        safe_file_name = "Az02-_/.txt"

        self.assertEqual(FileHelper.sanitize_name(dangerous_file_name), safe_file_name)

        # same names without the ending /
        dangerous_file_name = "\"Az02'{([$*!%?-_.txt"
        safe_file_name = "Az02-_.txt"
        file_store: FileStore = LocalFileStore()
        file_path = DataProvider.get_test_data_path("mini_travel_graph.json")
        # Add a file from a path
        file: File = file_store.add_file_from_path(file_path, dangerous_file_name)

        self.assertEqual(file.get_default_name(), safe_file_name)
