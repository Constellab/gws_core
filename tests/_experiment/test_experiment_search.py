

from gws_core.core.classes.search_builder import SearchParams
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_enums import (ExperimentStatus,
                                                  ExperimentType)
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.project.project import Project
from gws_core.test.base_test_case import BaseTestCase
from gws_core.test.gtest import GTest


class TestExperimentSearch(BaseTestCase):

    def test_search(self):
        experiment_1 = ExperimentService.create_experiment(
            title="My first experiment title world",
            type_=ExperimentType.TRANSFORMER)

        experiment_2: Experiment = ExperimentService.create_experiment(
            title="The second one world")
        experiment_2.mark_as_success()

        project: Project = GTest.create_default_project()
        experiment_2.project = project
        experiment_2.is_validated = True
        experiment_2.save()

        search_dict: SearchParams = SearchParams()

        # Test full text search
        search_dict.filtersCriteria = [{"key": "text", "operator": "MATCH", "value": "title"}]
        self.search(search_dict, 1)

        search_dict.filtersCriteria = [{"key": "text", "operator": "MATCH", "value": "world"}]
        self.search(search_dict, 2)

        # Test status search
        search_dict.filtersCriteria = [
            {"key": "status", "operator": "EQ", "value": ExperimentStatus.SUCCESS.value}]
        self.search(search_dict, 1)

        # Test type search
        search_dict.filtersCriteria = [
            {"key": "type", "operator": "EQ", "value": ExperimentType.TRANSFORMER.value}]
        self.search(search_dict, 1)

        # Test validate search
        search_dict.filtersCriteria = [{"key": "is_validated", "operator": "EQ", "value": True}]
        self.search(search_dict, 1)

        # Test with project
        search_dict.filtersCriteria = [{"key": "project", "operator": "IN", "value": [project.id]}]
        self.search(search_dict, 1)

    def search(self, search_dict: SearchParams, expected_nb_of_result: int) -> None:
        paginator = ExperimentService.search(search_dict).to_json()
        self.assertEqual(paginator['total_number_of_items'], expected_nb_of_result)
