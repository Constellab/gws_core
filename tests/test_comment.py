# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import (BaseTestCase, Comment, CommentService, File, GTest,
                      PaginatorDict, ResourceModel, Robot)


class TestComment(BaseTestCase):

    def test_comment(self):
        GTest.print("Comment")
        robot = Robot()
        resource_model: ResourceModel = ResourceModel.from_resource(robot).save_full()

        comment1 = CommentService.add_comment_to_model(resource_model, "The sky is blue")
        CommentService.add_comment_to_model(
            resource_model, "The sky is blue and the ocean is also blue", reply_to_id=comment1.id)
        CommentService.add_comment_to_model(resource_model, message="I want to go to Paris")

        page: PaginatorDict = CommentService.get_model_comments(resource_model).to_json()
        self.assertEqual(page['total_number_of_items'], 3)

        if Comment.get_db_manager().is_mysql_engine():
            query = Comment.search("sky")
            self.assertEqual(len(query), 2)
            for c in query:
                print(c.message)

            query = Comment.search("want paris", in_boolean_mode=False)
            self.assertEqual(len(query), 1)

            query = Comment.search("want paris", in_boolean_mode=True)
            self.assertEqual(len(query), 1)
            for c in query:
                print(c.message)

            query = Comment.search("want -paris", in_boolean_mode=True)
            self.assertEqual(len(query), 0)
