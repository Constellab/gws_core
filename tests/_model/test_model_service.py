

from gws_core import (BaseTestCase, ModelService, Paginator, ResourceModel,
                      Robot)
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
            CONST_RESOURCE_MODEL_TYPING_NAME, resource_model.id)
        self.assertIsNotNone(resource_model_db)

        # Test the find paginated
        resource_models: Paginator[ResourceModel] = ModelService.fetch_list_of_models(CONST_RESOURCE_MODEL_TYPING_NAME)
        self.assertEqual(resource_models.page_info.total_number_of_items, 1)
