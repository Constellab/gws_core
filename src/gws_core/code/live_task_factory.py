

from typing import List

from gws_core.brick.brick_helper import BrickHelper
from gws_core.code.task_generator import TaskGenerator
from gws_core.config.param.param_spec import (BoolParam, FloatParam, IntParam,
                                              ParamSpec, StrParam)
from gws_core.core.utils.numeric_helper import NumericHelper
from gws_core.impl.live.py_live_task import PyLiveTask
from gws_core.task.task_model import TaskModel


class LiveTaskFactory:

    @classmethod
    def generate_task_code_from_live_task_id(cls, task_id: str) -> str:
        task: TaskModel = TaskModel.get_by_id_and_check(task_id)

        if task.get_process_type() != PyLiveTask:
            raise Exception(f"The task {task_id} is not a python live task")

        return cls.generate_task_code_from_live_task(task)

    @classmethod
    def generate_task_code_from_live_task(cls, task: TaskModel) -> str:

        task_generator: TaskGenerator = TaskGenerator(task.instance_name)

        code: str = task.config.get_value(PyLiveTask.CONFIG_CODE_NAME)

        cleaned_code: str = ''
        for code_line in code.splitlines():
            # if the line is an import
            if code_line.startswith('import') or code_line.startswith('from'):
                task_generator.add_import(code_line)
            else:
                cleaned_code = cleaned_code + code_line + '\n'

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

        params: List[str] = task.config.get_value(PyLiveTask.CONFIG_PARAMS_NAME)
        for param_line in params:
            if not param_line or '=' not in param_line or '#' in param_line or param_line[0] == '#':
                continue

            param_line = param_line.strip()
            param_line = param_line.replace(' ', '')

            param_name = param_line.split('=')[0]
            param_value = param_line.split('=')[1]

            param_type: ParamSpec = None
            # detect if type if int, float, bool or str based on value
            if param_value == 'True' or param_value == 'False':
                param_type = BoolParam(bool(param_value))
            elif NumericHelper.is_int(param_value):
                param_type = IntParam(int(param_value))
            elif NumericHelper.is_float(param_value):
                param_type = FloatParam(float(param_value))
            else:
                param_type = StrParam(str(param_value))

            task_generator.add_config_spec(param_name, param_type)

        return task_generator.generate_code()

    @classmethod
    def generate_live_task_file_from_live_task_id(cls, task_id: str) -> dict:
        task: TaskModel = TaskModel.get_by_id_and_check(task_id)
        values = task.config.get_and_check_values()
        code = task.config.get_value("code")
        params = ''
        if values.get("params") is not None:
            params = '\n'.join(task.config.get_value("params"))
        env = ""
        if values.get("env") is not None:
            env = task.config.get_value("env")
        inputs = task.inputs.get_specs_as_dict()
        outputs = task.outputs.get_specs_as_dict()

        brick_versions = BrickHelper.get_all_brick_versions()
        bricks = []

        for brick_version in brick_versions:
            brick_name = brick_version.name
            brick_version = brick_version.version
            if brick_name in code:
                bricks.append({
                    "name": brick_name,
                    "version": brick_version
                })

        return {
            "json_version": 1,
            "params": params,
            "code": code,
            "environment": env,
            "input_specs": inputs,
            "output_specs": outputs,
            "config_specs": {},
            "bricks": bricks,
            "task_type": cls.get_live_task_type(task.instance_name),
        }

    @classmethod
    def get_live_task_type(cls, instance_name: str) -> str:
        choice = {
            'PyLiveTask': 'PYTHON',
            'PyCondaLiveTask': 'CONDA_PYTHON',
            'PyMambaLiveTask': 'MAMBA_PYTHON',
            'PyPipenvLiveTask': 'PIP_PYTHON',
            'RCondaLiveTask': 'CONDA_R',
            'RMambaLiveTask': 'MAMBA_R',
            'StreamlitLiveTask': 'STREAMLIT',
        }
        return choice[instance_name.split('_')[0]]
