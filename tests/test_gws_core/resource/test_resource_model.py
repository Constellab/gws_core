

from gws_core import (BaseTestCase, ConfigParams, File, OutputSpec,
                      OutputSpecs, Resource, ResourceModel, RField,
                      ScenarioProxy, Task, TaskInputs, TaskModel, TaskOutputs,
                      TaskProxy, resource_decorator, task_decorator)
from gws_core.config.config_specs import ConfigSpecs
from gws_core.core.classes.search_builder import (SearchFilterCriteria,
                                                  SearchOperator, SearchParams)
from gws_core.impl.robot.robot_resource import Robot
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_service import ResourceService
from gws_core.test.data_provider import DataProvider


@resource_decorator(unique_name="ForSearch")
class ForSearch(Resource):

    searchable_text: str = RField(searchable=True)

    @classmethod
    def create(cls, text) -> 'ForSearch':
        for_search = ForSearch()
        for_search.searchable_text = text
        return for_search


@task_decorator("ForSearchCreate")
class ForSearchCreate(Task):
    output_specs = OutputSpecs({'search': OutputSpec(ForSearch)})
    config_specs = ConfigSpecs({})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {'search': ForSearch.create('empty')}


@resource_decorator(unique_name="SubFile")
class SubFile(File):
    pass


# test_resource_model
class TestResourceModel(BaseTestCase):

    def test_search_by_name(self):
        resource = Robot.empty()
        resource.name = "test"
        resource_model = ResourceModel.save_from_resource(resource, origin=ResourceOrigin.UPLOADED)

        resource_2 = Robot.empty()
        resource_2.name = "anotherresource"
        resource_model_2 = ResourceModel.save_from_resource(resource_2, origin=ResourceOrigin.UPLOADED)

        result = ResourceService.search_by_name("test")
        self.assertEqual(result.page_info.total_number_of_items, 1)
        self.assertEqual(result.results[0].id, resource_model.id)

        result = ResourceService.search_by_name("herresour")
        self.assertEqual(result.page_info.total_number_of_items, 1)
        self.assertEqual(result.results[0].id, resource_model_2.id)

    def test_search(self):
        # Create a scenario and a task
        scenario: ScenarioProxy = ScenarioProxy()
        scenario.get_protocol().add_process(ForSearchCreate, 'facto')
        task: TaskProxy = scenario.get_protocol().get_process('facto')

        self._create_resource(
            'this is information about a great banana',
            ResourceOrigin.GENERATED, task._process_model)
        self._create_resource('the weather is not so great today', ResourceOrigin.UPLOADED)

        search_dict: SearchParams = SearchParams()

        # Search on name resource typing name
        search_dict.set_filters_criteria([
            SearchFilterCriteria(
                key="resource_typing_name", operator=SearchOperator.EQ,
                value=ForSearch.get_typing_name())])
        self._search(search_dict, 2)

        # Search on name ResourceOrigin
        search_dict.set_filters_criteria([
            SearchFilterCriteria(key="origin", operator=SearchOperator.EQ, value=ResourceOrigin.GENERATED.value)])
        self._search(search_dict, 1)

        # Search on Scenario
        search_dict.set_filters_criteria([
            SearchFilterCriteria(key="scenario", operator=SearchOperator.EQ, value=scenario._scenario.id)])
        self._search(search_dict, 1)

        # Search on Task
        search_dict.set_filters_criteria([
            SearchFilterCriteria(key="task_model", operator=SearchOperator.EQ, value=task._process_model.id)])
        self._search(search_dict, 1)

        # Search on Data with full text
        search_dict.set_filters_criteria([self._get_data_filter("information")])
        self._search(search_dict, 1)
        search_dict.set_filters_criteria([self._get_data_filter("great")])
        self._search(search_dict, 2)
        search_dict.set_filters_criteria([self._get_data_filter("gre*")])
        self._search(search_dict, 2)

    def _search(self, search_dict: SearchParams, expected_nb_of_result: int) -> None:
        paginator = ResourceService.search(search_dict).to_dto()
        self.assertEqual(
            paginator.total_number_of_items, expected_nb_of_result)

    def test_upload_and_delete(self):
        file: File = DataProvider.get_new_empty_file()

        resource_model: ResourceModel = ResourceModel.save_from_resource(
            file, origin=ResourceOrigin.UPLOADED)
        ResourceService.delete(resource_model.id)

        self.assertIsNone(ResourceModel.get_by_id(resource_model.id))

    def test_update_type(self):
        file: File = DataProvider.get_new_empty_file()

        resource_model: ResourceModel = ResourceModel.save_from_resource(
            file, origin=ResourceOrigin.UPLOADED)
        self.assertIsInstance(resource_model.get_resource(), File)
        self.assertNotIsInstance(resource_model.get_resource(), SubFile)

        ResourceService.update_resource_type(
            resource_model.id, SubFile.get_typing_name())

        resource_model = ResourceModel.get_by_id_and_check(
            resource_model.id)
        self.assertIsInstance(resource_model.get_resource(), SubFile)

    def _get_tag_filter(self, value: str) -> SearchFilterCriteria:
        return SearchFilterCriteria(key='tags', operator=SearchOperator.CONTAINS, value=value)

    def _get_data_filter(self, value: str) -> SearchFilterCriteria:
        return SearchFilterCriteria(key='data', operator=SearchOperator.MATCH, value=value)

    def _create_resource(
            self, text: str,
            origin: ResourceOrigin, task: TaskModel = None) -> ResourceModel:
        for_search: ForSearch = ForSearch.create(text)
        resource_model = ResourceModel.from_resource(
            for_search, origin=ResourceOrigin.UPLOADED)
        resource_model.origin = origin

        if task:
            resource_model.task_model = task
            resource_model.scenario = task.scenario
        return resource_model.save()
