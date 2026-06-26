
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import IntParam
from gws_core.io.dynamic_io import DynamicInputs, DynamicOutputs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource import Resource
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.resource.resource_set.resource_list_base import ResourceListBase
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator(
    unique_name="ResourceListStacker",
    short_description="Stack a set of resource in a resource list",
    hide=False,
    style=TypingStyle.material_icon("format_list_bulleted", background_color="#FEC7B4"),
)
class ResourceListStacker(Task):
    """
    Stack a set of resource in a resource list.
    This is useful when a task uses a resource list as input.

    The provided input resource are directly added to the output resource list (resource are not copied).

    If an input resource is a ResourceList or a ResourceSet, the resource are flatten and added to the output resource list.
    """

    input_specs: InputSpecs = DynamicInputs()
    output_specs: OutputSpecs = OutputSpecs({"resource_list": OutputSpec(ResourceList)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        resource_list = inputs.get_resource("source", ResourceList)

        output_resource_list: ResourceList = ResourceList()

        for i, resource in enumerate(resource_list):
            if resource is not None:
                if isinstance(resource, ResourceListBase):
                    # prevent nesting resource lists
                    self.log_info_message(
                        f"Flatten sub resource for resource {str(i + 1)} because it is a resource list or set"
                    )
                    for sub_resource in resource.get_resources_as_set():
                        output_resource_list.add_resource(sub_resource, create_new_resource=False)
                else:
                    self.log_info_message(f"Adding resource {str(i + 1)}")
                    output_resource_list.add_resource(resource, create_new_resource=False)

        if len(output_resource_list) == 0:
            raise Exception("No resource found in the input")

        return {"resource_list": output_resource_list}


@task_decorator(
    unique_name="ResourceListPicker",
    short_description="Pick a resource from a resource list",
    hide=False,
    style=TypingStyle.material_icon("format_list_bulleted", background_color="#FEC7B4"),
)
class ResourceListPicker(Task):
    """
    Pick a resource from a resource list.

    This is useful when you need to extract a resource from a resource list to use it in another

    The picked resource references the original resource in the resource list and is not a copy.

    """

    input_specs: InputSpecs = InputSpecs(
        {
            "resource_list": InputSpec(ResourceList),
        }
    )
    output_specs: OutputSpecs = DynamicOutputs(
        additionnal_port_spec=OutputSpec(Resource, sub_class=True)
    )

    config_specs = ConfigSpecs(
        {
            "indexes": ParamSet(
                ConfigSpecs(
                    {
                        "index": IntParam(
                            human_name="Resource index",
                            short_description="The index (starting at 0) of the resource to pick",
                        )
                    }
                ),
                human_name="Resource indexes",
                short_description="The indexes of the resources to pick",
            )
        }
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        resource_list = inputs.get_resource("resource_list", ResourceList)
        configs: list[dict] = params.get_value("indexes")

        output_resource_list = ResourceList()

        for config in configs:
            if config.get("index") is not None:
                resource = resource_list[config["index"]]
                resource.set_as_reference()
                output_resource_list.add_resource(resource)

        return {"target": output_resource_list}
