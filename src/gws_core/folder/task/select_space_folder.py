from gws_core.config.config_params import ConfigParams
from gws_core.folder.space_folder import SpaceFolder
from gws_core.folder.task.space_folder_param import SpaceFolderParam
from gws_core.folder.task.space_folder_resource import SpaceFolderResource
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import OutputSpecs
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator("SelectSpaceFolder", human_name="Select a space folder",
                short_description="Select a space folder and return a SpaceFolderResource")
class SelectSpaceFolder(Task):

    output_specs = OutputSpecs({
        'space_folder': OutputSpec(SpaceFolderResource, human_name="Selected space folder")
    })

    config_specs = {
        'space_folder': SpaceFolderParam(human_name="Select a space folder"),
    }

    OUTPUT_NAME = 'space_folder'
    CONFIG_NAME = 'space_folder'

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        space_folder: SpaceFolder = params.get_value('space_folder')

        return {'space_folder': SpaceFolderResource(space_folder.id)}
