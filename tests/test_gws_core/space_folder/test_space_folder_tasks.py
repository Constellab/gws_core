from gws_core.config.config_specs import ConfigSpecs
from gws_core.folder.space_folder import SpaceFolder
from gws_core.folder.task.select_space_folder import SelectSpaceFolder
from gws_core.folder.task.space_folder_param import SpaceFolderParam
from gws_core.folder.task.space_folder_resource import SpaceFolderResource
from gws_core.task.task_runner import TaskRunner
from gws_core.test.base_test_case import BaseTestCase


# test_space_folder_tasks
class TestSpaceFolderParam(BaseTestCase):
    def test_space_folder_params(self):
        space_folder = SpaceFolder(name="Test")
        space_folder.save()

        config_params = ConfigSpecs({"space_folder": SpaceFolderParam()}).build_config_params(
            {"space_folder": space_folder.id}
        )

        data: SpaceFolder = config_params["space_folder"]
        self.assertIsInstance(data, SpaceFolder)
        self.assertEqual(data.id, space_folder.id)
        self.assertEqual(data.name, "Test")

    def test_select_space_folder(self):
        space_folder = SpaceFolder(name="Test 2")
        space_folder.save()

        task_runner = TaskRunner(SelectSpaceFolder, params={"space_folder": space_folder.id})
        result = task_runner.run()

        space_folder_resource: SpaceFolderResource = result["space_folder"]
        self.assertIsInstance(space_folder_resource, SpaceFolderResource)
        self.assertEqual(space_folder_resource.space_folder_id, space_folder.id)
        self.assertEqual(space_folder_resource.get_space_folder().name, "Test 2")
