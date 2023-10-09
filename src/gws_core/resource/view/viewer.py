# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import Type

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import DictParam, StrParam
from gws_core.core.utils.utils import Utils
from gws_core.io.io_spec import InputSpec
from gws_core.io.io_specs import InputSpecs
from gws_core.model.typing_manager import TypingManager
from gws_core.resource.resource import Resource
from gws_core.resource.view.view_runner import ViewRunner
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator('Viewer', human_name="Viewer", short_description="Show a configured view")
class Viewer(Task):
    """Special task to configure and show a view in a protocol
    """

    input_name: str = 'resource'
    resource_config_name: str = 'resource_typing_name'
    view_config_name: str = 'view_config'

    input_specs: InputSpecs = InputSpecs({
        "resource": InputSpec(Resource)
    })

    config_specs: ConfigSpecs = {
        "resource_typing_name": StrParam(),
        "view_config": DictParam()
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        from gws_core.resource.resource_service import ResourceService
        from gws_core.resource.view_config.view_config_service import \
            ViewConfigService

        resource = inputs.get('resource')

        config_resource_type: Type[Resource] = TypingManager.get_type_from_name(params.get('resource_typing_name'))
        if not Utils.issubclass(type(resource), config_resource_type):
            raise Exception(
                f"The input resource type '{resource._human_name}' is not compatible with the type provided in the config: '{config_resource_type._human_name}'")

        resource_model = ResourceService.get_resource_by_id(resource._model_id)

        view_config = params.get('view_config')
        view_method_name = view_config['view_method_name']
        config_values = view_config['config_values']

        view_runner: ViewRunner = ViewRunner(resource, view_method_name, config_values)
        view = view_runner.generate_view()

        # save the view config as flagged
        ViewConfigService.save_view_config(
            resource_model=resource_model,
            view=view,
            view_name=view_method_name,
            config=view_runner.get_config(),
            flagged=True)

        return {}
