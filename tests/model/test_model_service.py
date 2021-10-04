

from gws_core import ResourceModel, Robot
from gws_core.core.classes.paginator import Paginator
from gws_core.core.test.base_test_case import BaseTestCase
from gws_core.model.model_service import ModelService
from gws_core.resource.resource_model import CONST_RESOURCE_MODEL_TYPING_NAME


class TestModelService(BaseTestCase):

    def test_get_models(self):

        resource_model: ResourceModel = ResourceModel.from_resource(Robot.empty())
        resource_model.save()

        # Test the count
        count: int = ModelService.count_model(CONST_RESOURCE_MODEL_TYPING_NAME)
        self.assertEqual(count, 1)

        # Test the find one
        resource_model_db: ResourceModel = ModelService.fetch_model(
            CONST_RESOURCE_MODEL_TYPING_NAME, resource_model.uri)
        self.assertIsNotNone(resource_model_db)

        # Test the find paginated
        resource_models: Paginator[ResourceModel] = ModelService.fetch_list_of_models(CONST_RESOURCE_MODEL_TYPING_NAME)
        self.assertEqual(resource_models.total_number_of_items, 1)
