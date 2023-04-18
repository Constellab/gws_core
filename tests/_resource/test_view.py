# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import (BaseTestCase, ConfigParams, IntParam, JSONView, Resource,
                      ResourceService, StrParam, TextView, resource_decorator,
                      view)
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import ParamSpec
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.resource.resource_model import ResourceModel, ResourceOrigin
from gws_core.resource.view.any_view import AnyView
from gws_core.resource.view.lazy_view_param import LazyViewParam
from gws_core.resource.view.view_helper import ViewHelper
from gws_core.resource.view.view_meta_data import ResourceViewMetaData
from gws_core.resource.view.view_types import ViewType
from gws_core.resource.view.viewer import Viewer
from gws_core.resource.view_config.view_config import ViewConfig
from gws_core.resource.view_config.view_config_service import ViewConfigService


# test_view
@resource_decorator("ResourceViewTest")
class ResourceViewTest(Resource):

    @view(view_type=TextView, human_name='View for test', short_description='Description for test',
          default_view=True)
    def a_view_test(self, params: ConfigParams) -> TextView:
        text_view = TextView('Test sub')
        text_view.set_title('Sub view title')
        return text_view


@resource_decorator("ResourceViewTestSub")
class ResourceViewTestSub(ResourceViewTest):

    @view(view_type=TextView, human_name='Sub View for test', short_description='Description for sub test',
          specs={'test_str_param': StrParam(default_value='Hello'),
                 'test_any_param': StrParam('Nice')},
          default_view=True)
    def sub_view_test(self, params: ConfigParams) -> TextView:
        text_view = TextView(params.get_value('test_str_param') + params.get_value('test_any_param'))
        text_view.set_title('Sub view title')
        return text_view


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
          specs={"lazy": LazyViewParam('get_param', StrParam())})
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
        view: TextView = ViewHelper.generate_view_on_resource(
            resource, 'sub_view_test',
            {"test_str_param": "Bonjour ", "test_any_param": '12', "page": 1, "page_size": 5000})

        self.assertEqual(view._type, TextView._type)
        self.assertEqual(view._data, "Bonjour 12")
        self.assertEqual(view.get_title(), "Sub view title")

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

        resource = resource_model.get_resource()
        view_meta = ViewHelper.get_and_check_view_meta(type(resource), 'a_view_test')
        specs: ConfigSpecs = view_meta.get_view_specs_from_resource(resource, skip_private=True)

        # if the page was overrided and the private is working, the page should not be in the json
        self.assertFalse('page' in specs)

    def test_get_view_specs(self):
        resource: Resource = ResourceLazySpecs()
        resource_model: ResourceModel = ResourceModel.from_resource(resource, origin=ResourceOrigin.UPLOADED)

        # call with a resource
        view_meta = ViewHelper.get_and_check_view_meta(type(resource), 'lazy_view')
        specs: ConfigSpecs = view_meta.get_view_specs_from_resource(resource_model.get_resource())

        self.assertEqual(len(specs), 1)
        self.assertTrue('lazy' in specs)
        self.assertIsInstance(specs['lazy'], StrParam)
        self.assertEqual(specs['lazy'].allowed_values, ['super'])

        # call with a resource type, like configuration before have the actual resource
        specs: ConfigSpecs = view_meta.get_view_specs_from_type(type(resource))

        self.assertEqual(len(specs), 1)
        self.assertTrue('lazy' in specs)
        self.assertIsInstance(specs['lazy'], StrParam)
        # there should be no allowed value
        self.assertIsNone(specs['lazy'].allowed_values)

    def test_view_config(self):

        resource: Resource = ResourceViewTestSub()
        resource_model: ResourceModel = ResourceModel.save_from_resource(resource, origin=ResourceOrigin.UPLOADED)

        view_result = ResourceService.get_and_call_view_on_resource_model(
            resource_model.id, 'a_view_test', {"page": 1, "page_size": 5000}, [], True)

        self.assertIsNotNone(view_result["view_config"])

        paginator = ViewConfigService.get_by_resource(resource_model.id)
        self.assertEqual(paginator.page_info.total_number_of_items, 1)

        view_config: ViewConfig = paginator.results[0]
        self.assertEqual(view_config.resource_model.id, resource_model.id)
        self.assertEqual(view_config.view_name, 'a_view_test')
        self.assertEqual(view_config.view_type, ViewType.TEXT)
        self.assertEqual(view_config.title, 'Sub view title')
        self.assert_json(view_config.config_values, {"page": 1, "page_size": 5000})
        self.assertEqual(view_config.transformers, [])

        # re-call the view from the view config
        view_result_2 = ResourceService.call_view_from_view_config(view_config.id)
        self.assert_json(view_result['view'], view_result_2['view'])

    def test_viewer(self):
        """ Test that a view config is save when executing the view task
        """
        resource: Resource = ResourceViewTestSub()
        resource_model: ResourceModel = ResourceModel.save_from_resource(resource, origin=ResourceOrigin.UPLOADED)

        # create an experiment with the view task
        i_experiment = IExperiment()
        i_protocol = i_experiment.get_protocol()

        view_config = {'view_method_name': 'a_view_test', 'config_values': {
            "page": 1, "page_size": 5000}, 'transformers': []}
        viewer = i_protocol.add_process(Viewer, 'viewer', {
            Viewer.resource_config_name: resource._typing_name, 'view_config': view_config})

        i_protocol.add_source('source', resource_model.id, viewer << Viewer.input_name)
        i_experiment.run()

        # check that view config was saved
        view_configs: List[ViewConfig] = list(ViewConfig.get_by_resource(resource_model.id))
        self.assertEqual(len(view_configs), 1)
        self.assertTrue(view_configs[0].flagged)
