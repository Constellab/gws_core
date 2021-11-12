

from typing import List

from gws_core import BaseTestCase, Paginator, ResourceModel, Robot, Tag
from gws_core.core.classes.paginator import PaginatorDict
from gws_core.resource.resource_search_dto import ResourceSearchDTO
from gws_core.resource.resource_service import ResourceService


class TestResourceModel(BaseTestCase):

    def test_search(self):
        nameTag = Tag('name', 'test')
        otherTag = Tag('other', 'super')
        self._create_resource_with_tag([nameTag])
        self._create_resource_with_tag([nameTag, otherTag])

        # Search on name tag
        paginator = ResourceService.search(ResourceSearchDTO(tags=[nameTag])).to_json()
        self.assertEqual(paginator['total_number_of_items'], 2)

        # Search on both tag
        paginator = ResourceService.search(ResourceSearchDTO(tags=[nameTag, otherTag])).to_json()
        self.assertEqual(paginator['total_number_of_items'], 1)

    def _create_resource_with_tag(self, tags: List[Tag]) -> ResourceModel:
        robot: Robot = Robot.empty()
        resource_model = ResourceModel.from_resource(robot)
        resource_model.set_tags(tags)
        return resource_model.save()
