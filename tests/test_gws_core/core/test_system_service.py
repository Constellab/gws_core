

import os

from pandas import DataFrame

from gws_core import (BaseTestCase, File, FileHelper, KVStore, ResourceModel,
                      Settings, Table)
from gws_core.impl.file.fs_node_service import FsNodeService
from gws_core.impl.file.local_file_store import LocalFileStore
from gws_core.lab.system_service import SystemService
from gws_core.resource.resource_dto import ResourceOrigin


# test_system_service
class TestSystemService(BaseTestCase):

    def test_garbage_collector(self):
        temp_dir = Settings.get_instance().make_temp_dir()

        # create unused file in kvstore
        unused_file = os.path.join(KVStore.get_base_dir(), "unused_file.txt")
        FileHelper.create_empty_file_if_not_exist(unused_file)

        # create unused file in filestore
        unused_file_2_tmp_path = os.path.join(temp_dir, "unused_file_2.txt")
        FileHelper.create_empty_file_if_not_exist(unused_file_2_tmp_path)
        local_file_store: LocalFileStore = LocalFileStore.get_default_instance()
        unused_file_2: File = local_file_store.add_file_from_path(unused_file_2_tmp_path)

        # create simple table
        table = Table(DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]}))
        resource_model = ResourceModel.save_from_resource(table, origin=ResourceOrigin.UPLOADED)

        # create a file resource
        test_file_path = FileHelper.create_empty_file_if_not_exist(os.path.join(temp_dir, "test_file_1.txt"))
        new_file: File = File(test_file_path)
        file_model = FsNodeService.create_fs_node_model(new_file)
        self.assertTrue(FileHelper.exists_on_os(file_model.fs_node_model.path))

        # call garbage collector
        SystemService.garbage_collector()

        # Check that the temps dir has been deleted
        self.assertFalse(FileHelper.exists_on_os(temp_dir))

        # check that the unused file has been deleted
        self.assertFalse(FileHelper.exists_on_os(unused_file))

        # check that the resource kvstore still exists
        kv_store = KVStore(resource_model.kv_store_path)
        self.assertTrue(FileHelper.exists_on_os(kv_store.full_file_path))

        # check that the unused file in filestore has been deleted
        self.assertFalse(FileHelper.exists_on_os(unused_file_2.path))
        # check that the resource filestore still exists
        self.assertTrue(FileHelper.exists_on_os(file_model.fs_node_model.path))
