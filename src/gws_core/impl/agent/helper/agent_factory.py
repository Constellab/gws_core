from typing import Any, Dict

from gws_core.brick.brick_helper import BrickHelper
from gws_core.code.task_generator import TaskGenerator
from gws_core.community.community_dto import CommunityAgentFileDTO, CommunityAgentFileParams
from gws_core.config.param.dynamic_param import DynamicParam
from gws_core.config.param.param_spec import ParamSpec
from gws_core.impl.agent.py_agent import PyAgent
from gws_core.task.task_model import TaskModel


class AgentFactory:
    current_json_version = 3

    AGENT_DICT = {
        "TASK.gws_core.PyAgent": "PYTHON",
        "TASK.gws_core.PyCondaAgent": "CONDA_PYTHON",
        "TASK.gws_core.PyMambaAgent": "MAMBA_PYTHON",
        "TASK.gws_core.PyPipenvAgent": "PIP_PYTHON",
        "TASK.gws_core.RCondaAgent": "CONDA_R",
        "TASK.gws_core.RMambaAgent": "MAMBA_R",
        "TASK.gws_core.StreamlitAgent": "STREAMLIT",
        "TASK.gws_core.StreamlitCondaAgent": "STREAMLIT",
        "TASK.gws_core.StreamlitMambaAgent": "STREAMLIT",
        "TASK.gws_core.StreamlitPipenvAgent": "STREAMLIT",
    }

    @classmethod
    def generate_task_code_from_agent_id(cls, task_id: str) -> str:
        task: TaskModel = TaskModel.get_by_id_and_check(task_id)

        if task.get_process_type() != PyAgent:
            raise Exception(f"The task {task_id} is not a python agent")

        return cls.generate_task_code_from_agent(task)

    @classmethod
    def generate_task_code_from_agent(cls, task: TaskModel) -> str:
        task_generator: TaskGenerator = TaskGenerator(task.instance_name)

        code: str = task.config.get_value(PyAgent.CONFIG_CODE_NAME)

        cleaned_code: str = ""
        for code_line in code.splitlines():
            # if the line is an import
            if code_line.startswith("import") or code_line.startswith("from"):
                task_generator.add_import(code_line)
            else:
                cleaned_code = cleaned_code + code_line + "\n"

        task_generator.set_run_method_content(cleaned_code)

        count = 1
        for spec in task.inputs.get_specs().get_specs().values():
            key = f"resource_{count}"
            task_generator.add_input_spec(key, spec.get_default_resource_type())
            count = count + 1

        count = 1
        for spec in task.outputs.get_specs().get_specs().values():
            key = f"resource_{count}"
            task_generator.add_output_spec(key, spec.get_default_resource_type())
            count = count + 1

        params: Dict[str, Any] = task.config.get_value(PyAgent.CONFIG_PARAMS_NAME)
        params_spec: DynamicParam = task.config.get_spec(PyAgent.CONFIG_PARAMS_NAME)
        for param_name in params:
            param_value = params[param_name]

            param_type: ParamSpec = params_spec.specs.get_spec(param_name)
            param_type.default_value = param_value

            task_generator.add_config_spec(param_name, param_type)

        return task_generator.generate_code()

    @classmethod
    def generate_agent_file_from_agent_id(
        cls, task_id: str, with_value: bool = False
    ) -> CommunityAgentFileDTO:
        task: TaskModel = TaskModel.get_by_id_and_check(task_id)
        values = task.config.get_values()
        code = task.config.get_value("code")
        params = None
        if values.get("params") is not None:
            specs = (
                task.config.get_spec("params")
                .to_simple_dto()
                .to_json_dict()["additional_info"]["specs"]
            )
            params_values = task.config.get_value("params")
            if not with_value:
                for key in params_values.keys():
                    params_values[key] = None
            params = {"specs": specs, "values": params_values}
        env = ""
        if values.get("env") is not None:
            env = task.config.get_value("env")
        inputs = task.inputs.get_specs_as_dict()
        outputs = task.outputs.get_specs_as_dict()

        brick_versions = BrickHelper.get_all_brick_versions()
        bricks = []

        for brick_version in brick_versions:
            if brick_version.name in code:
                bricks.append({"name": brick_version.name, "version": brick_version.version})

        return CommunityAgentFileDTO.from_json(
            {
                "json_version": cls.current_json_version,
                "params": params
                if params is not None
                else CommunityAgentFileParams(specs={}, values={}).to_json_dict(),
                "code": code,
                "environment": env,
                "input_specs": inputs,
                "output_specs": outputs,
                "config_specs": {},
                "bricks": bricks,
                "task_type": cls.AGENT_DICT[task.process_typing_name],
                "style": task.to_dto().style,
            }
        )

    @classmethod
    def is_agent(cls, typing_name: str) -> bool:
        return typing_name in cls.AGENT_DICT
