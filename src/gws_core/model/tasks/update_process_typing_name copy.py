from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import StrParam
from gws_core.core.db.migration.sql_migrator import SqlMigrator
from gws_core.model.typing import Typing
from gws_core.model.typing_style import TypingStyle
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator("UpdateProcessTypingName", human_name="[Support] Update process typing name",
                short_description="Support task to update the typing name of processes in the database",
                style=TypingStyle.material_icon(material_icon_name='support_agent'))
class UpdateProcessTypingName(Task):
    """
    ⚠️⚠️⚠️ Use this task only if you know what you are doing, it can break the system.⚠️⚠️⚠️

    Update the typing name of processes (task or protocol) in the database.
    This is useful when the typing name of a process has changed after an update for example.
    """

    config_specs = ConfigSpecs({
        # this config is only set when calling this automatically
        "processes": ParamSet(ConfigSpecs({
            'old_name': StrParam(human_name="Old process typing name", short_description="Ex: TASK.gws_core.MyOldTaskUniqueName"),
            'new_name': StrParam(human_name="New process typing name", short_description="Ex: TASK.gws_core.MyNewTaskUniqueName"),
        }), human_name="Processes to update"),
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        processes = params.get_value("processes")

        for process in processes:
            old_name = process['old_name']
            new_name = process['new_name']

            try:
                SqlMigrator.rename_process_typing_name(Typing.get_db(), old_name, new_name)
            except Exception as e:
                self.log_error_message(f"Error while updating process typing name '{old_name}' to '{new_name}'")
                self.log_error_message(str(e))
            self.log_info_message(f"Process typing name '{old_name}' updated to '{new_name}'")

        return {}
