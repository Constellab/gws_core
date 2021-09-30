

from typing import List

from gws_core import (BaseTestCase, Resource, ResourceService,
                      resource_decorator, view)
from gws_core.config.param_spec import StrParam
from gws_core.resource.view_decorator import ResourceViewMetaData
from gws_core.resource.view_helper import ViewHelper


@resource_decorator("ResourceViewTest")
class ResourceViewTest(Resource):

    @view(human_name='View for test', short_description='Description for test',
          default_view=True)
    def a_view_test(self) -> str:
        return 'Test sub'

    @view(human_name='View for test', short_description='Description for test', specs={"test": StrParam()})
    def z_view_test(self, **kwargs) -> str:
        return kwargs.get('test')


@resource_decorator("ResourceViewTestSub")
class ResourceViewTestSub(ResourceViewTest):

    @view(human_name='Sub View for test', short_description='Description for sub test',
          specs={'test_str_param': StrParam(),
                 'test_any_param': StrParam()},
          default_view=True)
    def sub_view_test(self, test_str_param: str = 'Hello', test_any_param='Nice') -> str:
        return test_str_param + str(test_any_param)


class TestView(BaseTestCase):

    def test_view_def(self):
        views: List[ResourceViewMetaData] = ResourceService.get_views_of_resource_type(ResourceViewTest)

        self.assertEqual(len(views), 2)

        # get the view of view_test method
        view_test: ResourceViewMetaData = views[0]
        self.assertEqual(view_test.method_name, 'a_view_test')
        self.assertEqual(view_test.human_name, 'View for test')
        self.assertEqual(view_test.short_description, 'Description for test')
        self.assertEqual(view_test.default_view, True)

        # Test with inheritance
        views: List[ResourceViewMetaData] = ResourceService.get_views_of_resource_type(ResourceViewTestSub)
        self.assertEqual(len(views), 3)

        # Test that the first view is the one of the child and this is the only default
        sub_view_test: ResourceViewMetaData = [x for x in views if x.method_name == 'sub_view_test'][0]
        self.assertIsNotNone(sub_view_test)
        self.assertEqual(sub_view_test.default_view, True)

        view_test_2: ResourceViewMetaData = [x for x in views if x.method_name == 'a_view_test'][0]
        self.assertIsNotNone(view_test_2)
        self.assertEqual(view_test_2.default_view, False)

        # Test get default view
        default_view = ViewHelper.get_default_view_of_resource_type(ResourceViewTestSub)
        self.assertEqual(default_view.method_name, 'sub_view_test')

    def test_default_view(self):
        # Test get default view
        default_view = ViewHelper.get_default_view_of_resource_type(ResourceViewTestSub)
        self.assertEqual(default_view.method_name, 'sub_view_test')

        resource = ResourceViewTestSub()
        result = ResourceService.call_view_on_resource(resource, 'sub_view_test', None)
        self.assertEqual(result, 'HelloNice')

    def test_view_call(self):
        resource = ResourceViewTestSub()
        result = ResourceService.call_view_on_resource(
            resource, 'sub_view_test', {"test_str_param": "Bonjour ", "test_any_param": 12})

        self.assertEqual(result, "Bonjour 12")

        # test view with kwargs
        result = ResourceService.call_view_on_resource(
            resource, 'z_view_test', {"test": "Bonjour"})

        self.assertEqual(result, "Bonjour")
