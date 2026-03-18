from gws_core.config.config_params import ConfigParams, ConfigParamsDict
from gws_core.config.config_specs import ConfigSpecs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.lab.lab_model.lab_dto import LabDTOWithCredentials
from gws_core.lab.lab_model.lab_model_param import LabModelParam
from gws_core.model.typing_style import TypingStyle
from gws_core.scenario.scenario_enums import ScenarioStatus
from gws_core.scenario.scenario_waiter import ScenarioWaiterExternalLab
from gws_core.scenario.task.scenario_resource import ScenarioResource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService


@task_decorator(
    unique_name="ScenarioWaiterTask",
    human_name="Wait for external scenario",
    short_description="Wait for a scenario running in an external lab to finish",
    style=TypingStyle.material_icon("hourglass_empty"),
)
class ScenarioWaiterTask(Task):
    """
    Task that waits for a scenario running in an external lab to finish.

    This task polls the external lab API to check the scenario status and
    blocks until the scenario reaches a terminal state (SUCCESS, ERROR, etc.).

    It is used in the auto-run pipeline after SendScenarioToLab to wait for
    the scenario to complete before downloading outputs.
    """

    input_specs = InputSpecs(
        {
            "scenario": InputSpec(
                ScenarioResource,
                human_name="Scenario",
                short_description="The scenario running in the external lab",
            ),
        }
    )

    output_specs = OutputSpecs({"scenario": OutputSpec(ScenarioResource, human_name="Scenario")})

    config_specs = ConfigSpecs(
        {
            "lab": LabModelParam(
                human_name="External lab",
                short_description="The external lab to check the scenario status (must have credentials configured)",
            ),
        }
    )

    INPUT_NAME = "scenario"
    OUTPUT_NAME = "scenario"

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        scenario_resource: ScenarioResource = inputs[self.INPUT_NAME]
        scenario_id = scenario_resource.scenario_id

        lab_dto: LabDTOWithCredentials = params.get_value("lab")
        user_id = CurrentUserService.get_and_check_current_user().id

        self.log_info_message(f"Waiting for scenario '{scenario_id}' to finish in external lab")

        scenario_waiter = ScenarioWaiterExternalLab(scenario_id, lab_dto, user_id)

        # Wait indefinitely (max_count=-1) since run time is unpredictable
        scenario_info = scenario_waiter.wait_until_finished(
            refresh_interval=60,
            refresh_interval_max_count=-1,
            message_dispatcher=self.message_dispatcher,
        )

        if scenario_info.scenario.status != ScenarioStatus.SUCCESS:
            error = (
                scenario_info.progress.last_message.text
                if scenario_info.progress and scenario_info.progress.has_last_message()
                else "Unknown error"
            )
            raise Exception(
                f"External scenario failed, status: {scenario_info.scenario.status}. "
                f"Error details: {error}"
            )

        self.log_success_message(f"Scenario '{scenario_id}' finished successfully in external lab")

        # Unmark the local scenario as running in external lab
        scenario = scenario_resource.get_scenario().refresh()
        scenario.unmark_running_in_external_lab()

        return {self.OUTPUT_NAME: scenario_resource}

    @classmethod
    def build_config(
        cls,
        lab: str,
    ) -> ConfigParamsDict:
        return {
            "lab": lab,
        }
