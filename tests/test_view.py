

from typing import Dict, List

from gws_core import (BaseTestCase, Resource, ResourceService, StrParam,
                      TextView, resource_decorator, view)
from gws_core.config.param_spec import StrParam
from gws_core.resource.view import View
from gws_core.resource.view_decorator import ResourceViewMetaData
from gws_core.resource.view_helper import ViewHelper
from gws_core.resource.view_types import ViewConfig


@resource_decorator("ResourceViewTest")
class ResourceViewTest(Resource):

    @view(view_type=TextView, human_name='View for test', short_description='Description for test',
          default_view=True)
    def a_view_test(self) -> TextView:
        return TextView('Test sub')

    @view(view_type=TextView, human_name='View for test', short_description='Description for test',
          specs={"test": StrParam()})
    def z_view_test(self, **kwargs) -> TextView:
        return TextView(kwargs.get('test'))


@resource_decorator("ResourceViewTestSub")
class ResourceViewTestSub(ResourceViewTest):

    @view(view_type=TextView, human_name='Sub View for test', short_description='Description for sub test',
          specs={'test_str_param': StrParam(default_value='Hello'),
                 'test_any_param': StrParam('Nice')},
          default_view=True)
    def sub_view_test(self, test_str_param: str, test_any_param) -> TextView:
        return TextView(test_str_param + str(test_any_param))


class TestView(BaseTestCase):

    def test_view_def(self):
        views: List[ResourceViewMetaData] = ResourceService.get_views_of_resource_type(ResourceViewTest)

        self.assertEqual(len(views), 3)

        # get the view of view_test method
        view_test: ResourceViewMetaData = [x for x in views if x.method_name == 'a_view_test'][0]
        self.assertEqual(view_test.method_name, 'a_view_test')
        self.assertEqual(view_test.human_name, 'View for test')
        self.assertEqual(view_test.short_description, 'Description for test')
        self.assertEqual(view_test.default_view, True)

        # Test with inheritance
        views: List[ResourceViewMetaData] = ResourceService.get_views_of_resource_type(ResourceViewTestSub)
        self.assertEqual(len(views), 4)

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

    def test_call_view_method(self):
        resource = ResourceViewTestSub()
        view_: View = ViewHelper.call_view_method(
            resource, 'sub_view_test', {"test_str_param": "Bonjour ", "test_any_param": 12})

        self.assertEqual(view_._data, "Bonjour 12")

        # test view with kwargs
        view_ = ViewHelper.call_view_method(
            resource, 'z_view_test', {"test": "Bonjour"})

        self.assertEqual(view_._data, "Bonjour")

    def test_test_complete_call_view(self):
        resource = ResourceViewTestSub()
        config: ViewConfig = {
            "method_config": {"test_str_param": "Bonjour ", "test_any_param": 12},
            "view_config": {"page": 1, "page_size": 5000}}
        dict_: Dict = ViewHelper.call_view_on_resource(
            resource, 'sub_view_test', config)

        self.assertEqual(dict_["type"], TextView._type)
        self.assertEqual(dict_["data"], "Bonjour 12")

        # Test with pagination
        config = {
            "method_config": {"test_str_param": "Bonjour ", "test_any_param": 12},
            "view_config": {"page": 2, "page_size": 5}}
        dict_ = ViewHelper.call_view_on_resource(
            resource, 'sub_view_test', config)

        self.assertEqual(dict_["data"], "ur 12")
