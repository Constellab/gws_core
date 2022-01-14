

from typing import Dict, List

from gws_core import (BaseTestCase, ConfigParams, IntParam, JSONView, Resource,
                      ResourceService, StrParam, TextView, resource_decorator,
                      view)
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param_spec import ParamSpec
from gws_core.resource.any_view import AnyView
from gws_core.resource.lazy_view_param import LazyViewParam
from gws_core.resource.resource_model import ResourceModel, ResourceOrigin
from gws_core.resource.view_helper import ViewHelper
from gws_core.resource.view_meta_data import ResourceViewMetaData
from gws_core.resource.view_types import ViewCallResult


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


@resource_decorator("ResourceViewTestOverideParent")
class ResourceViewTestOverideParent(Resource):

    @view(view_type=TextView, human_name='View overide',
          specs={"page": IntParam(default_value=1, min_value=0, human_name="Page number", visibility='private')})
    def a_view_test(self, params: ConfigParams) -> TextView:
        return TextView('Test sub')


@resource_decorator("ResourceViewTestOveride")
class ResourceViewTestOveride(ResourceViewTestOverideParent):

    @view(view_type=TextView, human_name='View overide',
          specs={"page": IntParam(default_value=1, min_value=0, human_name="Page number", visibility='public')})
    def a_view_test(self, params: ConfigParams) -> TextView:
        return TextView('Test sub')

    @view(view_type=TextView, hide=True)
    def view_as_json(self, params: ConfigParams) -> JSONView:
        """Disable the view
        """
        pass


@resource_decorator("ResourceLazySpecs")
class ResourceLazySpecs(Resource):

    allowed_value = ['super']

    @view(view_type=AnyView, human_name='View overide',
          specs={"lazy": LazyViewParam('get_param')})
    def lazy_view(self, params: ConfigParams) -> AnyView:
        return AnyView('Test sub')

    def get_param(self) -> StrParam:
        return StrParam(allowed_values=self.allowed_value)


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
        view_result: ViewCallResult = ViewHelper.call_view_on_resource(
            resource, 'sub_view_test',
            {"test_str_param": "Bonjour ", "test_any_param": '12', "page": 1, "page_size": 5000})

        self.assertEqual(view_result["view_human_name"], "Sub View for test")
        self.assertEqual(view_result["view_short_description"], "Description for sub test")
        self.assertEqual(view_result["view_data"]["type"], TextView._type)
        self.assertEqual(view_result["view_data"]["data"]['text'], "Bonjour 12")

    def test_method_view_override_and_hide(self):
        """Test that the spec of a view are overrided but the children method. And check if hide param in view decorator works
        """

        views: List[ResourceViewMetaData] = ViewHelper.get_views_of_resource_type(ResourceViewTestOveride)

        view_test: ResourceViewMetaData = [x for x in views if x.method_name == 'a_view_test'][0]
        # the child class should have overwritten the page parameter to make is visible
        self.assertEqual(view_test.specs['page'].visibility, 'public')

        # the view as json should be hidden and not returned by the list view
        self.assertEqual(len([x for x in views if x.method_name == 'view_as_json']), 0)

    def test_view_spec_override_and_private(self):
        """Test a method view where spec override view specs and private visiblity"""

        resource: Resource = ResourceViewTestOverideParent()
        resource_model: ResourceModel = ResourceModel.from_resource(resource, origin=ResourceOrigin.UPLOADED)

        specs: ConfigSpecs = ViewHelper.get_view_specs(resource_model, 'a_view_test')

        # if the page was overrided and the private is working, the page should not be in the json
        self.assertFalse('page' in specs)

    def test_get_view_specs(self):
        resource: Resource = ResourceLazySpecs()
        resource_model: ResourceModel = ResourceModel.from_resource(resource, origin=ResourceOrigin.UPLOADED)

        specs: ConfigSpecs = ViewHelper.get_view_specs(resource_model, 'lazy_view')

        self.assertEqual(len(specs), 1)
        self.assertTrue('lazy' in specs)
        self.assertIsInstance(specs['lazy'], ParamSpec)
        self.assertEqual(specs['lazy'].allowed_values, ['super'])
