# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from typing_extensions import ParamSpec

from gws_core.code.task_generator import TaskGenerator
from gws_core.config.param.param_spec import (BoolParam, FloatParam, IntParam,
                                              StrParam)
from gws_core.core.utils.numeric_helper import NumericHelper
from gws_core.impl.live.py_live_task import PyLiveTask
from gws_core.task.task_model import TaskModel


class TaskGeneratorService:

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
            spec.get_default_resource_type
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
