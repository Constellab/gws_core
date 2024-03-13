

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.impl.file.file import File
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.resource.resource import Resource
from gws_core.resource.resource_zipper import ResourceZipper
from gws_core.resource.technical_info import TechnicalInfo
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User


@task_decorator("ResourceZipper", human_name="Zip resource",
                short_description="Zip a resource object to be downloaded by another lab")
class ResourceZipperTask(Task):

    input_name = 'source'
    output_name = 'target'

    input_specs: InputSpecs = InputSpecs({
        "source": InputSpec(Resource, human_name="Resource to zip")
    })

    output_specs: OutputSpecs = OutputSpecs({
        "target": OutputSpec(File, human_name="Zip file")
    })

    config_specs: ConfigSpecs = {
        # this config is only set when calling this automatically
        "shared_by_id": StrParam(optional=True, human_name="Id of the user that shared the resource",
                                 visibility=StrParam.PRIVATE_VISIBILITY),
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        shared_by_id = params.get_value("shared_by_id")

        shared_by: User = None
        if shared_by_id:
            shared_by = User.get_by_id(shared_by_id)

            if not shared_by:
                raise Exception(f"User with id {shared_by_id} not found")
        else:
            shared_by = CurrentUserService.get_and_check_current_user()

        origin_entity_id = inputs['source']._model_id
        resource_zipper = ResourceZipper(shared_by)
        resource_zipper.add_resource_model(origin_entity_id)
        resource_zipper.close_zip()

        file_path = resource_zipper.get_zip_file_path()

        file = File(file_path)
        # store information about the entity that generated the zip file
        file.add_technical_info(TechnicalInfo("origin_entity_type", EntityType.RESOURCE.value))
        file.add_technical_info(TechnicalInfo("origin_entity_id", origin_entity_id))

        return {"target": file}
