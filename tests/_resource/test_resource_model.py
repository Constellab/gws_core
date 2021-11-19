

from typing import List

from gws_core import (BaseTestCase, ConfigParams, Resource, ResourceModel, Tag,
                      Task, TaskInputs, TaskModel, TaskOutputs,
                      resource_decorator, task_decorator)
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.resource.r_field import RField
from gws_core.resource.resource_model import ResourceOrigin
from gws_core.resource.resource_search_dto import ResourceSearchDTO
from gws_core.resource.resource_service import ResourceService
from gws_core.tag.tag import TagHelper
from gws_core.task.task_interface import ITask


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
                                       nameTag, otherTag], ResourceOrigin.IMPORTED)

        # Search on name tag
        paginator = ResourceService.search(ResourceSearchDTO(tags=str(nameTag))).to_json()
        self.assertEqual(paginator['total_number_of_items'], 2)
        # Search on both tag
        paginator = ResourceService.search(ResourceSearchDTO(tags=TagHelper.tags_to_str([nameTag, otherTag]))).to_json()
        self.assertEqual(paginator['total_number_of_items'], 1)
        # Search on name tag
        paginator = ResourceService.search(ResourceSearchDTO(tags='name')).to_json()
        self.assertEqual(paginator['total_number_of_items'], 2)

        # Search on name tag & resource typing name
        paginator = ResourceService.search(ResourceSearchDTO(
            tags=str(nameTag), resource_typing_name=ForSearch._typing_name)).to_json()
        self.assertEqual(paginator['total_number_of_items'], 2)

        # Search on name tag & ResourceOrigin
        paginator = ResourceService.search(ResourceSearchDTO(
            tags=str(nameTag), origin=ResourceOrigin.GENERATED.value)).to_json()
        self.assertEqual(paginator['total_number_of_items'], 1)

        # Search on Experiment
        paginator = ResourceService.search(ResourceSearchDTO(experiment_id=experiment._experiment.id)).to_json()
        self.assertEqual(paginator['total_number_of_items'], 1)

        # Search on Task
        paginator = ResourceService.search(ResourceSearchDTO(task_id=task._task_model.id)).to_json()
        self.assertEqual(paginator['total_number_of_items'], 1)

        # Search on Data with full text
        paginator = ResourceService.search(ResourceSearchDTO(data="information")).to_json()
        self.assertEqual(paginator['total_number_of_items'], 1)
        paginator = ResourceService.search(ResourceSearchDTO(data="great")).to_json()
        self.assertEqual(paginator['total_number_of_items'], 2)
        paginator = ResourceService.search(ResourceSearchDTO(data="gre*")).to_json()
        self.assertEqual(paginator['total_number_of_items'], 2)

    def _create_resource_with_tag(
            self, text: str,  tags: List[Tag],
            origin: ResourceOrigin, task: TaskModel = None) -> ResourceModel:
        for_search: ForSearch = ForSearch.create(text)
        resource_model = ResourceModel.from_resource(for_search, origin=ResourceOrigin.IMPORTED)
        resource_model.set_tags(tags)
        resource_model.origin = origin

        if task:
            resource_model.task_model = task
            resource_model.experiment = task.experiment
        return resource_model.save()
