# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import unittest

from gws_core import Comment, CommentService, File, GTest


class TestComment(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()

    def test_comment(self):
        GTest.print("Comment")
        f = File(path="./oui")
        c1 = f.add_comment("The sky is blue")
        c2 = f.add_comment(
            "The sky is blue and the ocean is also blue", reply_to=c1)
        f.save()
        c3 = CommentService.add_comment(
            object_uri=f.uri,
            object_type=f.type,
            message="I want to go to Paris"
        )

        self.assertEqual(len(f.comments), 3)
        for c in f.comments:
            if c == c1:
                self.assertEqual(c.message, "The sky is blue")
            if c == c2:
                self.assertEqual(
                    c.message, "The sky is blue and the ocean is also blue")
            if c == c3:
                self.assertEqual(c.message, "I want to go to Paris")

        if Comment.get_db_manager().is_mysql_engine():
            Q = Comment.search("sky")
            self.assertEqual(len(Q), 2)
            for c in Q:
                print(c.message)

            Q = Comment.search("want paris", in_boolean_mode=False)
            self.assertEqual(len(Q), 1)

            Q = Comment.search("want paris", in_boolean_mode=True)
            self.assertEqual(len(Q), 1)
            for c in Q:
                print(c.message)

            Q = Comment.search("want -paris", in_boolean_mode=True)
            self.assertEqual(len(Q), 0)
