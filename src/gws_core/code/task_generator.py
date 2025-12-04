import inspect
from typing import Dict, List, Set, Type

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import ParamSpec
from gws_core.core.utils.string_helper import StringHelper
from gws_core.core.utils.utils import Utils
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.resource.resource import Resource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs


class TaskGenerator:
    """Class use to generate code for a task"""

    class_name: str = ""

    inputs_specs: Dict[str, Type[Resource]] = None
    outputs_specs: Dict[str, Type[Resource]] = None
    config_specs: ConfigSpecs = None

    run_method_content: str = None
    custom_imports: List[str] = None
    gws_core_additional_imports: Set[str] = None

    _TASK_OUTPUTS_TYPE = "TaskOutputs"

    _INPUT_SPECS_NAME = "input_specs"
    _OUTPUT_SPECS_NAME = "output_specs"
    _CONFIG_SPECS_NAME = "config_specs"

    def __init__(self, class_name: str) -> None:
        self.class_name = StringHelper.to_pascal_case(class_name)
        self.inputs_specs = {}
        self.outputs_specs = {}

        self.config_specs = ConfigSpecs({})
        self.run_method_content = ""
        self.custom_imports = []
        self.gws_core_additional_imports = set()

    def set_run_method_content(self, run_method_content: str) -> None:
        """Set the content of the run method

        :param run_method_content: The content of the run method
        :type run_method_content: str
        """
        self.run_method_content = run_method_content

    def add_import(self, import_name: str) -> None:
        """Add a custom import

        :param import_name: The name of the import
        :type import_name: str
        """
        self.custom_imports.append(import_name)

    def add_input_spec(self, key: str, resource_type: Type[Resource]) -> None:
        """Add an input spec

        :param key: The key of the input spec
        :type key: str
        :param resource_type: Type of the resource
        :type resource_type: Type[Resource]
        """
        if not Utils.issubclass(resource_type, Resource):
            raise Exception(
                f"The resource type {resource_type.__name__} is not a subclass of Resource"
            )
        self.inputs_specs[key] = resource_type

        # add required imports, by default the type is Resource
        self.gws_core_additional_imports.add(resource_type.__name__)
        self.gws_core_additional_imports.add(InputSpec.__name__)

    def add_output_spec(self, key: str, resource_type: Type[Resource]) -> None:
        """Add an output spec

        :param key: The key of the output spec
        :type key: str
        :param resource_type: Type of the resource
        :type resource_type: Type[Resource]
        """
        if not Utils.issubclass(resource_type, Resource):
            raise Exception(
                f"The resource type {resource_type.__name__} is not a subclass of Resource"
            )
        self.outputs_specs[key] = resource_type

        # add required imports, by default the type is Resource
        self.gws_core_additional_imports.add(resource_type.__name__)
        self.gws_core_additional_imports.add(OutputSpec.__name__)

    def add_config_spec(self, key: str, param_spec: ParamSpec) -> None:
        """Add a config spec

        :param key: The key of the config spec
        :type key: str
        :param param_spec: Type of the param spec
        :type param_spec: Type[ParamSpec]
        """

        if not isinstance(param_spec, ParamSpec):
            raise Exception(f"The param spec {param_spec.__name__} is not a instance of ParamSpec")
        self.config_specs.add_spec(key, param_spec)

        # add required imports,
        self.gws_core_additional_imports.add(param_spec.__class__.__name__)

    ######################################### GENERATE #########################################

    def generate_code(self) -> str:
        """Generate the code for a task

        :return: The code for a task
        :rtype: str
        """

        str_class = f"""
{self._build_imports()}


{self._build_class_name()}

{self._build_input_specs()}
{self._build_output_specs()}
{self._build_config_specs()}

{self._build_run_method()}

"""
        return str_class

    ######################################## IMPORTS ########################################

    def _build_imports(self) -> str:
        return f"""{self._build_gws_core_import()}
{self._build_custom_imports()}"""

    def _build_gws_core_import(self) -> str:
        required_imports = [
            Task.__name__,
            InputSpecs.__name__,
            OutputSpecs.__name__,
            ConfigSpecs.__name__,
            ConfigParams.__name__,
            TaskInputs.__name__,
            self._TASK_OUTPUTS_TYPE,
            task_decorator.__name__,
        ]

        required_imports.extend(self.gws_core_additional_imports)
        required_imports.sort()

        return f"from gws_core import ({', '.join(required_imports)})"

    def _build_custom_imports(self) -> str:
        return "\n".join(self.custom_imports)

    def _build_class_name(self) -> str:
        return f"""@{task_decorator.__name__}(unique_name="{self.class_name}")
class {self.class_name}(Task):"""

    ########################################### IO ###########################################

    def _build_input_specs(self) -> str:
        return f"""\t{self._INPUT_SPECS_NAME}: {InputSpecs.__name__} = {InputSpecs.__name__}({self._build_io_spec_dict(self.inputs_specs, InputSpec.__name__)})"""

    def _build_output_specs(self) -> str:
        return f"""\t{self._OUTPUT_SPECS_NAME}: {OutputSpecs.__name__} = {OutputSpecs.__name__}({self._build_io_spec_dict(self.outputs_specs, OutputSpec.__name__)})"""

    def _build_io_spec_dict(self, dict_: Dict[str, Type[Resource]], type_name: str) -> str:
        if len(dict_) == 0:
            return "{}"

        params: list = []
        for key, value in dict_.items():
            params.append(f"'{key}': {type_name}({value.__name__})")

        return self._build_list_to_json(params)

    ###################################### CONFIG SPECS ######################################

    def _build_config_specs(self) -> str:
        return f"""\t{self._CONFIG_SPECS_NAME} : {ConfigSpecs.__name__} = {ConfigSpecs.__name__}({self._build_config_specs_dict()})"""

    def _build_config_specs_dict(self) -> str:
        if len(self.config_specs) == 0:
            return "{}"

        params: list = []
        for key, value in self.config_specs.specs.items():
            default_value = value.get_default_value()
            str_default_value = (
                f"'{default_value}'" if isinstance(default_value, str) else f"{default_value}"
            )
            params.append(f"'{key}': {value.__class__.__name__}(default_value={str_default_value})")

        return self._build_list_to_json(params)

    def _build_list_to_json(self, list_: List[str]) -> str:
        return f"{{{', '.join(list_)}}}"

    ######################################### RUN ###########################################

    def _build_run_method(self) -> str:
        # convert the task run method signature to a string
        task_run_signature = inspect.signature(Task.run)

        params = ""
        for param in task_run_signature.parameters.values():
            if param.name == "self":
                params = "self"
            else:
                params += f", {param.name}: {param.annotation.__name__}"
        task_run_signature_string = (
            f"def {Task.run.__name__}({params}) -> {self._TASK_OUTPUTS_TYPE}:"
        )

        method_content = self.run_method_content if self.run_method_content else "pass"

        # append \t\t to each line of the method content
        method_content = "\n\t\t".join(method_content.splitlines())

        return f"""\t{task_run_signature_string}{method_content}"""
