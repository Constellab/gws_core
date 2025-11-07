
from gws_core.brick.brick_service import BrickService
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.code_param.json_code_param import JsonCodeParam
from gws_core.config.param.code_param.yaml_code_param import YamlCodeParam
from gws_core.config.param.param_spec import BoolParam, StrParam
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.docker.docker_dto import DockerComposeStatus
from gws_core.impl.file.file import File
from gws_core.impl.json.json_dict import JSONDict
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from .docker_service import DockerService


@task_decorator(
    unique_name="StartDockerComposeTask",
    human_name="Start Docker Compose Task",
    short_description="Start a Docker Compose from YAML configuration",
)
class StartDockerComposeTask(Task):
    """
    # Start Docker Compose Task

    A task that starts a Docker Compose service from YAML configuration.

    ## Overview

    This task allows you to deploy and start Docker containers using Docker Compose configuration.
    It validates the existence of the specified brick, processes the YAML configuration, and
    initiates the Docker Compose deployment through the Docker service.

    ## Input/Output

    - **Inputs**:
      - `yaml_file` (optional): File resource containing Docker Compose YAML configuration
    - **Output**: `JSONDict` resource containing the Docker Compose operation response

    ## Configuration Parameters

    | Parameter | Type | Required | Description |
    |-----------|------|----------|-------------|
    | `yaml_config` | YamlCodeParam | Conditional | YAML configuration for Docker Compose (required if no file input provided) |
    | `brick_name` | StrParam | Yes | Name of the brick (must exist in the system) |
    | `unique_name` | StrParam | Yes | Unique identifier for this compose instance |

    ## Behavior

    1. **Input Priority**: If a file input is provided, it takes precedence over the config parameter
    2. **Validation**: Checks that either file input or config parameter contains YAML configuration
    3. **Brick Validation**: Verifies that the specified brick exists in the system
    4. **Deployment**: Starts the Docker Compose using the YAML configuration
    5. **Response**: Returns a structured JSON response with deployment status and output

    ## Output Format

    The output JSONDict contains:
    - `message`: Status message from the Docker service
    - `output`: Detailed output from the Docker Compose operation
    - `brick_name`: The brick name used for deployment
    - `unique_name`: The unique name assigned to this compose instance

    ## Exceptions

    - `BadRequestException`: Raised if:
      - Neither file input nor config parameter is provided
      - The specified brick does not exist
    - Docker service exceptions: May be raised during compose deployment

    ## Usage Options

    ### Option 1: Using File Input
    Connect a File resource containing your docker-compose.yml to the `yaml_file` input.
    The config `yaml_config` parameter can be left empty.

    ### Option 2: Using Config Parameter
    Leave the `yaml_file` input unconnected and provide the YAML configuration
    directly in the `yaml_config` parameter using the YAML code editor.

    ## Example YAML Configuration

    ```yaml
    # Example Docker Compose YAML configuration
    version: '3.8'
    services:
      web:
        image: nginx:latest
        ports:
          - "80:80"
        environment:
          - ENV_VAR=value
    ```
    """

    input_specs: InputSpecs = InputSpecs({
        'yaml_file': InputSpec(File, human_name='Docker Compose YAML File',
                               short_description='Optional YAML file for Docker Compose configuration',
                               optional=True)
    })

    output_specs: OutputSpecs = OutputSpecs({
        'response': OutputSpec(JSONDict, human_name='Docker Compose Response',
                               short_description='Response from Docker Compose start operation')
    })

    config_specs = ConfigSpecs({
        'yaml_config': YamlCodeParam(human_name='Docker Compose YAML',
                                     short_description='YAML configuration for Docker Compose (used if no file input provided)',
                                     optional=True),
        'brick_name': StrParam(human_name='Brick Name',
                               short_description='Name of the brick',
                               optional=False),
        'unique_name': StrParam(human_name='Unique Name',
                                short_description='Unique name for the compose',
                                optional=False),
        'description': StrParam(human_name='Description',
                                short_description='Description of the compose instance',
                                optional=False),
        'env': JsonCodeParam(human_name='Environment Variables',
                             short_description='Optional environment variables for the compose as JSON object. Must be a Dict[str, str]'),
        'auto_start': BoolParam(human_name='Auto Start',
                                short_description='Whether to automatically start the compose on lab start',
                                default_value=False)
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        brick_name: str = params.get_value('brick_name')
        unique_name: str = params.get_value('unique_name')

        # Get YAML content from file input or config parameter
        yaml_file: File = inputs.get('yaml_file')
        if yaml_file is not None:
            # Use file content
            yaml_config = yaml_file.read()
        else:
            # Use config parameter
            yaml_config: str = params.get_value('yaml_config')
            if not yaml_config:
                raise BadRequestException("Either 'yaml_file' input or 'yaml_config' parameter must be provided")

        # Check that the brick exists
        brick_model = BrickService.get_brick_model(brick_name)
        if brick_model is None:
            raise BadRequestException(f"Brick '{brick_name}' does not exist")

        # check that env is a dict of str to str if provided
        env = params.get_value('env')
        if env is not None:
            if not isinstance(env, dict):
                raise BadRequestException("Environment variables must be a dictionary")

            for k, v in env.items():
                if not isinstance(k, str) or not isinstance(v, str):
                    raise BadRequestException("Environment variable keys and values must be strings")

        # Start the Docker Compose
        docker_service = DockerService()

        docker_service.register_and_start_compose(
            brick_name=brick_name,
            unique_name=unique_name,
            compose_yaml_content=yaml_config,
            description=params.get_value('description'),
            env=env,
            auto_start=params.get_value('auto_start')
        )

        self.log_info_message("Docker Compose started, waiting for ready status...")
        response = docker_service.wait_for_compose_status(
            brick_name=brick_name,
            unique_name=unique_name,
            max_attempts=20,
            message_dispatcher=self.message_dispatcher
        )

        if response.composeStatus.status != DockerComposeStatus.UP:
            text = f"Docker Compose did not start successfully, status: {response.composeStatus.status.value}."
            if response.composeStatus.info:
                text += f" Info: {response.composeStatus.info}."
            raise Exception(text)

        # Create JSON output
        json_dict = JSONDict()
        json_dict.data = {
            'status': response.composeStatus.status.value,
            'info': response.composeStatus.info,
            'brick_name': brick_name,
            'unique_name': unique_name
        }

        return {
            'response': json_dict
        }
