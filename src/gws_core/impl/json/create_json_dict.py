from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.code_param.json_code_param import JsonCodeParam
from gws_core.impl.json.json_dict import JSONDict
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator(
    "CreateJsonDict", human_name="Create json dict", short_description="Create a json dict resource"
)
class CreateJsonDict(Task):
    """Simple task to create a json dict resource from the interface.

    It can be useful to pass configuration to other tasks.

    Is uses a json code editor as configuration to create the json dict resource.
    """

    input_specs: InputSpecs = InputSpecs()
    output_specs: OutputSpecs = OutputSpecs(
        {
            "json_dict": OutputSpec(
                JSONDict, human_name="Json dict", short_description="Generated json dict resource"
            ),
        }
    )
    config_specs = ConfigSpecs({"json": JsonCodeParam(human_name="Json code", optional=False)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        json_dict = JSONDict()
        json_dict.data = params.get_value("json")
        return {"json_dict": json_dict}
