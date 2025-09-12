from enum import Enum
from typing import List

import typer
from typing_extensions import Annotated

from gws_cli.utils.cli_utils import CLIUtils
from gws_core import BrickService
from gws_core.manage import AppManager

app = typer.Typer(help="Manage server operations - run server, execute tests, run scenarios and processes")


class LogLevel(str, Enum):
    INFO = "INFO"
    DEBUG = "DEBUG"
    ERROR = "ERROR"


MAIN_SETTINGS_FILE_DEFAULT_PATH = "/lab/.sys/app/settings.json"

MainSettingFilePathAnnotation = Annotated[str, typer.Option('--settings-path', help="Path to the main settings file.")]
ShowSqlAnnotation = Annotated[bool, typer.Option("--show-sql", help="Log sql queries in the console.", is_flag=True)]
IsTestAnnotation = Annotated[bool, typer.Option("--test", help="Run in test mode.", is_flag=True)]


@app.command("run", help="Start the server")
def run(
        ctx: typer.Context,
        port: Annotated[str, typer.Option(help="Server port.")] = "3000",
        main_setting_file_path: MainSettingFilePathAnnotation = MAIN_SETTINGS_FILE_DEFAULT_PATH,
        show_sql: ShowSqlAnnotation = False):

    AppManager.start_app(
        main_setting_file_path=main_setting_file_path,
        port=port,
        log_level=CLIUtils.get_global_option_log_level(ctx),
        show_sql=show_sql)


@app.command("test", help="Run tests for a specific brick or all bricks")
def test(
        ctx: typer.Context,
        test_name: Annotated[List[str], typer.Argument(help="The name test file to launch (regular expression). Enter 'all' to launch all the tests.")],
        brick_name: Annotated[str, typer.Option("--brick-name", help="Name of the brick to test. If not provided, use brick of current folder.")] = None,
        show_sql: ShowSqlAnnotation = False):

    brick_dir: str
    if brick_name:
        brick_dir = BrickService.find_brick_folder(brick_name)
        print(f"Running tests for brick '{brick_dir}'")
    else:
        print("No brick dir provided. Using current directory.")
        brick_dir = CLIUtils.get_and_check_current_brick_dir()

    AppManager.run_test(
        brick_dir=brick_dir,
        tests=test_name,
        log_level=CLIUtils.get_global_option_log_level(ctx),
        show_sql=show_sql)


@app.command("run-scenario", help="Execute a specific scenario by ID")
def run_exp(
        ctx: typer.Context,
        scenario_id: Annotated[str, typer.Option("--scenario-id", help="Id of the scenario to run.")],
        user_id: Annotated[str, typer.Option("--user-id", help="Id of the user that run the scenario.")],
        main_setting_file_path: MainSettingFilePathAnnotation = MAIN_SETTINGS_FILE_DEFAULT_PATH,
        show_sql: ShowSqlAnnotation = False,
        is_test: IsTestAnnotation = False):
    AppManager.run_scenario(
        main_setting_file_path=main_setting_file_path,
        scenario_id=scenario_id,
        user_id=user_id,
        log_level=CLIUtils.get_global_option_log_level(ctx),
        show_sql=show_sql,
        is_test=is_test)


@app.command("run-process", help="Execute a specific process within a scenario")
def run_process(
        ctx: typer.Context,
        scenario_id: Annotated[str, typer.Option("--scenario-id", help="Id of the scenario to run.")],
        protocol_model_id: Annotated[str, typer.Option("--protocol-model-id", help="Id of the protocol model.")],
        process_instance_name: Annotated[str, typer.Option("--process-instance-name", help="Name of the process instance.")],
        user_id: Annotated[str, typer.Option("--user-id", help="Id of the user that run the process.")],
        main_setting_file_path: MainSettingFilePathAnnotation = MAIN_SETTINGS_FILE_DEFAULT_PATH,
        show_sql: ShowSqlAnnotation = False,
        is_test: IsTestAnnotation = False):
    AppManager.run_process(
        main_setting_file_path=main_setting_file_path,
        scenario_id=scenario_id,
        protocol_model_id=protocol_model_id,
        process_instance_name=process_instance_name,
        user_id=user_id,
        log_level=CLIUtils.get_global_option_log_level(ctx),
        show_sql=show_sql,
        is_test=is_test)
