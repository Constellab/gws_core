

import inspect
from typing import List

from gws_core import (BaseTestCase, Resource, ResourceService, Robot,
                      resource_decorator, view)
from gws_core.resource.view_decorator import ResourceViewMetaData


@resource_decorator("ResourceViewTest")
class ResourceViewTest(Resource):

    @view(human_name='View for test', short_description='Description for test')
    def view_test(self, test_str_param: str, test_any_param) -> str:
        return 'Test'


class TestView(BaseTestCase):

    def test_view(self,):
        views: List[ResourceViewMetaData] = ResourceService.get_view_of_resource_type(ResourceViewTest)

        self.assertEqual(len(views), 1)

        # get the view of view_test method
        view_test: ResourceViewMetaData = views[0]
        self.assertEqual(view_test.method_name, 'view_test')
        self.assertEqual(view_test.human_name, 'View for test')
        self.assertEqual(view_test.short_description, 'Description for test')
