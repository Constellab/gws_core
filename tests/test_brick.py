
from typing import Dict, List

from gws_core.brick.brick_helper import BrickHelper
from gws_core.brick.brick_model import BrickModel
from gws_core.brick.brick_service import BrickService
from gws_core.core.classes.jsonable import ListJsonable
from gws_core.core.utils.settings import ModuleInfo
from gws_core.task.task import Task
from gws_core.test.base_test_case import BaseTestCase


class TestBrick(BaseTestCase):

    def test_get_all_bricks(self):

        bricks_info: Dict[str, ModuleInfo] = BrickHelper.get_all_bricks()

        self.assertTrue(len(bricks_info) > 0)
        self.assertTrue('gws_core' in bricks_info)

    def test_get_obj_brick(self):

        brick_name: str = BrickHelper.get_brick_name(Task)
        self.assertEqual(brick_name, 'gws_core')

        brick_name = BrickHelper.get_brick_name(Task.run)
        self.assertEqual(brick_name, 'gws_core')

        brick_path: str = BrickHelper.get_brick_path(Task)
        self.assertIsNotNone(brick_path)

    def test_brick_models(self):
        brick_models: List[BrickModel] = BrickService.get_all_brick_models()
        self.assertTrue(len(brick_models) > 0)

        self.assertIsNotNone(ListJsonable(brick_models).to_json())

    def test_log_brick_message(self):
        BrickService.log_brick_message(Task, 'Test message', 'ERROR')

        brick_model = BrickService.get_brick_model('gws_core')
        self.assertEqual(brick_model.status, 'ERROR')
        self.assertTrue(len(brick_model.messages) > 0)