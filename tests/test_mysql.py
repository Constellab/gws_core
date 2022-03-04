# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import unittest

from gws_core import (BaseTestCase, File, FSNodeModel, FsNodeService, GTest,
                      LocalFileStore, MySQLService)
from gws_core.comment.comment_service import CommentService


class TestMySQLDumpLoad(BaseTestCase):

    def test_db_dump_load(self):

        # insert data in comment table
        file: File = LocalFileStore.get_default_instance().create_empty_file("./oui")
        file_model: FSNodeModel = FsNodeService.create_fs_node_model(fs_node=file)

        comment = CommentService.add_comment_to_model(file_model, "The sky is blue")
        CommentService.add_comment_to_model(
            file_model, "The sky is blue and the ocean is also blue", reply_to_id=comment.id)
        file_model.save()

        # dump db
        output_file = MySQLService.dump_db(
            "gws_core", force=True, wait=True)
        self.assertTrue(os.path.exists(output_file))

        GTest.drop_tables()
        self.assertFalse(FSNodeModel.table_exists())

        # load db
        MySQLService.load_db(
            "gws_core", local_file_path=output_file, force=True, wait=True)
        self.assertTrue(FSNodeModel.table_exists())

    def test_db_drop(self):
        pass
