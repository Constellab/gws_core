# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import unittest
from gws.comment import Comment
from gws.file import File
from gws.service.comment_service import CommentService
from gws.unittest import GTest

class TestComment(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        tables = (File, Comment )
        GTest.drop_tables(tables)
        GTest.init()
        pass

    @classmethod
    def tearDownClass(cls):
        tables = ( File, Comment )
        GTest.drop_tables(tables)
        pass
    
    def test_comment(self):
        GTest.print("Test Comment")

        f = File(path="./oui")
        c = f.add_comment("This my file comment")
        f.add_comment("This my file comment 2", reply_to=c)
        f.save()
        c = CommentService.add_comment(
            object_uri = f.uri, 
            object_type = f.type,
            text = "This my file comment 3"
            )

        self.assertTrue(f.comments[0], "This my file comment")
        self.assertTrue(f.comments[1], "This my file comment 2")
        self.assertTrue(f.comments[2], "This my file comment 3")
