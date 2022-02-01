

from typing import List

from gws_core import (BaseTestCase, ConfigParams, File, IExperiment, ITask,
                      Resource, ResourceModel, RField, TableFile, Tag, Task,
                      TaskInputs, TaskModel, TaskOutputs, resource_decorator,
                      task_decorator)
from gws_core.core.classes.search_builder import (SearchDict,
                                                  SearchFilterCriteria)
from gws_core.data_provider.data_provider import DataProvider
from gws_core.resource.resource_model import ResourceOrigin
from gws_core.resource.resource_service import ResourceService
from gws_core.tag.tag import TagHelper


@resource_decorator(unique_name="ForSearch")
class ForSearch(Resource):

    searchableText: str = RField(searchable=True)

    @classmethod
    def create(cls, text) -> 'ForSearch':
        for_search = ForSearch()
        for_search.searchableText = text
        return for_search


@task_decorator("ForSearchCreate")
class ForSearchCreate(Task):
    input_specs = {}  # no required input
    output_specs = {'search': ForSearch}
    config_specs = {}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {'search': ForSearch.create('empty')}


class TestResourceModel(BaseTestCase):

    def test_search(self):
        # Create an experiment and a task
        experiment: IExperiment = IExperiment()
        experiment.get_protocol().add_process(ForSearchCreate, 'facto')
        task: ITask = experiment.get_protocol().get_process('facto')

        nameTag = Tag('name', 'test')
        otherTag = Tag('other', 'super')
        self._create_resource_with_tag(
            'this is information about a great banana', [nameTag],
            ResourceOrigin.GENERATED, task._task_model)
        self._create_resource_with_tag('the weather is not so great today', [
                                       nameTag, otherTag], ResourceOrigin.UPLOADED)

        search_dict: SearchDict = SearchDict()

        # Search on name tag
        search_dict.filtersCriteria = [self._get_tag_filter(str(nameTag))]
        self.search(search_dict, 2)
        # Search on both tag
        search_dict.filtersCriteria = [self._get_tag_filter(TagHelper.tags_to_str([nameTag, otherTag]))]
        self.search(search_dict, 1)
        # Search on name tag
        search_dict.filtersCriteria = [self._get_tag_filter('name')]
        self.search(search_dict, 2)

        # Search on name tag & resource typing name
        search_dict.filtersCriteria = [
            self._get_tag_filter(str(nameTag)),
            {"key": "resource_typing_name", "operator": "EQ", "value": ForSearch._typing_name}]
        self.search(search_dict, 2)

        # Search on name tag & ResourceOrigin
        search_dict.filtersCriteria = [
            self._get_tag_filter(str(nameTag)),
            {"key": "origin", "operator": "EQ", "value": ResourceOrigin.GENERATED.value}]
        self.search(search_dict, 1)

        # Search on Experiment
        search_dict.filtersCriteria = [{"key": "experiment", "operator": "EQ", "value": experiment._experiment.id}]
        self.search(search_dict, 1)

        # Search on Task
        search_dict.filtersCriteria = [{"key": "task_model", "operator": "EQ", "value": task._task_model.id}]
        self.search(search_dict, 1)

        # Search on Data with full text
        search_dict.filtersCriteria = [self._get_data_filter("information")]
        self.search(search_dict, 1)
        search_dict.filtersCriteria = [self._get_data_filter("great")]
        self.search(search_dict, 2)
        search_dict.filtersCriteria = [self._get_data_filter("gre*")]
        self.search(search_dict, 2)

    def _get_tag_filter(self, value: str) -> SearchFilterCriteria:
        return {'key': 'tags', 'operator': 'CONTAINS', 'value': value}

    def _get_data_filter(self, value: str) -> SearchFilterCriteria:
        return {'key': 'data', 'operator': 'MATCH', 'value': value}

    def _create_resource_with_tag(
            self, text: str,  tags: List[Tag],
            origin: ResourceOrigin, task: TaskModel = None) -> ResourceModel:
        for_search: ForSearch = ForSearch.create(text)
        resource_model = ResourceModel.from_resource(for_search, origin=ResourceOrigin.UPLOADED)
        resource_model.set_tags(tags)
        resource_model.origin = origin

        if task:
            resource_model.task_model = task
            resource_model.experiment = task.experiment
        return resource_model.save()

    def search(self, search_dict: SearchDict, expected_nb_of_result: int) -> None:
        paginator = ResourceService.search(search_dict).to_json()
        self.assertEqual(paginator['total_number_of_items'], expected_nb_of_result)

    def test_upload_and_delete(self):
        file: File = DataProvider.get_iris_file()

        resource_model: ResourceModel = ResourceModel.save_from_resource(file, origin=ResourceOrigin.UPLOADED)
        ResourceService.delete(resource_model.id)

        self.assertIsNone(ResourceModel.get_by_id(resource_model.id))

    def test_update_type(self):
        file: File = DataProvider.get_iris_file()

        resource_model: ResourceModel = ResourceModel.save_from_resource(file, origin=ResourceOrigin.UPLOADED)
        self.assertIsInstance(resource_model.get_resource(), File)
        self.assertNotIsInstance(resource_model.get_resource(), TableFile)

        ResourceService.update_resource_type(resource_model.id, TableFile._typing_name)

        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource_model.id)
        self.assertIsInstance(resource_model.get_resource(), TableFile)
