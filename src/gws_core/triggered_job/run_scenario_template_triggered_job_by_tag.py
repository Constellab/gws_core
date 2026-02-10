from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.scenario_template.scenario_template_service import ScenarioTemplateService
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.triggered_job.triggered_job_dto import CreateTriggeredJobFromTemplateDTO
from gws_core.triggered_job.triggered_job_service import TriggeredJobService


@task_decorator(
    "RunScenarioTemplateTriggeredJobByTag",
    human_name="Run Scenario Template Triggered Job by Tag",
    short_description="Create a triggered job from a scenario template identified by tag"
)
class RunScenarioTemplateTriggeredJobByTag(Task):
    """
    Task to create a triggered job from a scenario template.
    The template is identified by a tag specified in the configuration.
    """

    config_specs = ConfigSpecs({
        "tag_key": StrParam(
                human_name="Tag key",
                short_description="Tag key to identify the scenario template",
                optional=False
            ),
        "tag_value": StrParam(
                human_name="Tag value",
                short_description="Tag value to identify the scenario template",
                optional=False
            ),
        "cron_expression": StrParam(
                human_name="Cron expression",
                short_description="Cron expression for scheduling the job (e.g., */10 * * * * for every 10 minutes)",
                optional=False,
                default_value="*/10 * * * *"
            )
    })

    def run(self, params: ConfigParams, inputs) -> dict:
        # Get the tag key and value from params to find the scenario template
        tag_key = params["tag_key"]
        tag_value = params["tag_value"]
        cron_expression = params["cron_expression"]

        # Get the scenario template using the tag
        scenario_template = ScenarioTemplateService.get_by_tag(
            tag_key=tag_key,
            tag_value=tag_value
        )

        # Create the triggered job from the template
        create_job_dto = CreateTriggeredJobFromTemplateDTO(
            scenario_template_id=scenario_template.id,
            name=f"Triggered job from template: {scenario_template.name}",
            description=f"Scheduled job from scenario template tagged with {tag_key}={tag_value}",
            cron_expression=cron_expression,
            config_values={},
            is_active=True
        )

        TriggeredJobService.create_from_template(create_job_dto)

        return {}
