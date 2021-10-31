

from typing import Dict, List

from gws_core import (BaseTestCase, ConfigParams, IntParam, Resource,
                      ResourceService, StrParam, TextView, resource_decorator,
                      view)
from gws_core.config.param_spec import StrParam
from gws_core.resource.view import View
from gws_core.resource.view_helper import ViewHelper
from gws_core.resource.view_meta_data import ResourceViewMetaData


@resource_decorator("ResourceViewTest")
class ResourceViewTest(Resource):

    @view(view_type=TextView, human_name='View for test', short_description='Description for test',
          default_view=True)
    def a_view_test(self, params: ConfigParams) -> TextView:
        return TextView('Test sub')


@resource_decorator("ResourceViewTestSub")
class ResourceViewTestSub(ResourceViewTest):

    @view(view_type=TextView, human_name='Sub View for test', short_description='Description for sub test',
          specs={'test_str_param': StrParam(default_value='Hello'),
                 'test_any_param': StrParam('Nice')},
          default_view=True)
    def sub_view_test(self, params: ConfigParams) -> TextView:
        return TextView(params.get_value('test_str_param') + params.get_value('test_any_param'))


@resource_decorator("ResourceViewTestOveride")
class ResourceViewTestOveride(Resource):

    @view(view_type=TextView, human_name='View overide',
          specs={"page": IntParam(default_value=1, min_value=0, human_name="Page number", visibility='private')})
    def a_view_test(self, params: ConfigParams) -> TextView:
        return TextView('Test sub')


class TestView(BaseTestCase):

    def test_view_def(self):
        views: List[ResourceViewMetaData] = ResourceService.get_views_of_resource_type(ResourceViewTest)

        self.assertEqual(len(views), 2)

        # get the view of view_test method
        view_test: ResourceViewMetaData = [x for x in views if x.method_name == 'a_view_test'][0]
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

    def test_complete_call_view(self):
        resource = ResourceViewTestSub()
        dict_: Dict = ViewHelper.call_view_on_resource(
            resource, 'sub_view_test',
            {"test_str_param": "Bonjour ", "test_any_param": '12', "page": 1, "page_size": 5000})

        self.assertEqual(dict_["type"], TextView._type)
        self.assertEqual(dict_["data"], "Bonjour 12")

    def test_method_view_override_and_private(self):
        """Test a method view where spec override view specs and private visiblity"""

        view_meta_data: ResourceViewMetaData = ViewHelper.get_and_check_view(ResourceViewTestOveride, 'a_view_test')

        self.assertTrue('page' in view_meta_data.view_type._specs)
        self.assertTrue('page' in view_meta_data.specs)
        json_ = view_meta_data.merge_visible_specs()

        # if the page was overrided and the private is working, the page should not be in the json
        self.assertFalse('page' in json_)
