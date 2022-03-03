# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import (BaseTestCase, CommentService, PaginatorDict,
                      ResourceModel, Robot)
from gws_core.resource.resource_model import ResourceOrigin


class TestComment(BaseTestCase):

    def test_comment(self):
        robot = Robot()
        resource_model: ResourceModel = ResourceModel.save_from_resource(robot, origin=ResourceOrigin.UPLOADED)

        comment1 = CommentService.add_comment_to_model(resource_model, "The sky is blue")
        CommentService.add_comment_to_model(
            resource_model, "The sky is blue and the ocean is also blue", reply_to_id=comment1.id)
        CommentService.add_comment_to_model(resource_model, message="I want to go to Paris")

        page: PaginatorDict = CommentService.get_model_comments(resource_model).to_json()
        self.assertEqual(page['total_number_of_items'], 3)
