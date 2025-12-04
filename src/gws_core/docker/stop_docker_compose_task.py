from gws_core.brick.brick_service import BrickService
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.impl.json.json_dict import JSONDict
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from .docker_service import DockerService


@task_decorator(
    unique_name="StopDockerComposeTask",
    human_name="Stop Docker Compose Task",
    short_description="Stop a running Docker Compose service",
)
class StopDockerComposeTask(Task):
    """
    # Stop Docker Compose Task

    A task that stops a running Docker Compose service identified by brick name and unique name.

    ## Overview

    This task allows you to stop and tear down Docker containers that were previously started
    using Docker Compose. It validates the existence of the specified brick and stops the
    Docker Compose deployment through the Docker service.


    ## Exceptions

    - `BadRequestException`: Raised if the specified brick does not exist
    - Docker service exceptions: May be raised during compose stop operation

    ## Usage Notes

    - The brick_name and unique_name must match those used when starting the compose
    - This task only stops the compose; it does not remove volumes or networks
    - Use this task to gracefully shut down Docker services before cleanup or redeployment

    ## Example

    To stop a compose that was started with brick_name="my_brick" and unique_name="web_service_1",
    use the same parameters in this task to stop it.
    """

    input_specs: InputSpecs = InputSpecs({})

    output_specs: OutputSpecs = OutputSpecs(
        {
            "response": OutputSpec(
                JSONDict,
                human_name="Docker Compose Stop Response",
                short_description="Response from Docker Compose stop operation",
            )
        }
    )

    config_specs = ConfigSpecs(
        {
            "brick_name": StrParam(
                human_name="Brick Name", short_description="Name of the brick", optional=False
            ),
            "unique_name": StrParam(
                human_name="Unique Name",
                short_description="Unique name for the compose instance to stop",
                optional=False,
            ),
        }
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        brick_name: str = params.get_value("brick_name")
        unique_name: str = params.get_value("unique_name")

        # Check that the brick exists
        brick_model = BrickService.get_brick_model(brick_name)
        if brick_model is None:
            raise BadRequestException(f"Brick '{brick_name}' does not exist")

        # Stop the Docker Compose
        docker_service = DockerService()
        response = docker_service.unregister_compose(brick_name=brick_name, unique_name=unique_name)

        # Create JSON output
        json_dict = JSONDict()
        json_dict.data = {
            "status": response.composeStatus.status.value,
            "info": response.composeStatus.info,
            "brick_name": brick_name,
            "unique_name": unique_name,
        }

        return {"response": json_dict}
