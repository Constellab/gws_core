import os
import subprocess
import sys
from enum import Enum
from typing import Annotated

import typer
from gws_core import BrickService
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.manage import AppManager
from gws_core.user.authorization_service import AuthorizationService

from gws_cli.utils.cli_utils import CLIUtils

app = typer.Typer(
    help="Manage server operations - run server, execute tests, run scenarios and processes"
)


class LogLevel(str, Enum):
    INFO = "INFO"
    DEBUG = "DEBUG"
    ERROR = "ERROR"


MainSettingFilePathAnnotation = Annotated[
    str, typer.Option("--settings-path", help="Path to the main settings file.")
]
ShowSqlAnnotation = Annotated[
    bool, typer.Option("--show-sql", help="Log sql queries in the console.", is_flag=True)
]
IsTestAnnotation = Annotated[bool, typer.Option("--test", help="Run in test mode.", is_flag=True)]


@app.command("run", help="Start the server")
def run(
    ctx: typer.Context,
    port: Annotated[str, typer.Option(help="Server port.")] = "3000",
    main_setting_file_path: MainSettingFilePathAnnotation = CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH,
    show_sql: ShowSqlAnnotation = False,
    allow_dev_app_connections: Annotated[
        bool,
        typer.Option(
            "--allow-dev-app-connections",
            help="Allow connections to the api from the apps running in dev mode.",
            is_flag=True,
        ),
    ] = False,
):
    if allow_dev_app_connections:
        if Settings.is_prod_mode():
            typer.echo(
                "Error: --allow-dev-app-connections cannot be used in production mode.", err=True
            )
            raise typer.Exit(code=1)
        Logger.warning("Dev mode app connections are allowed. Only use if you are working on apps.")
        AuthorizationService.allow_dev_app_connections = True

    AppManager.start_app(
        main_setting_file_path=main_setting_file_path,
        port=port,
        log_level=CLIUtils.get_global_option_log_level(ctx),
        show_sql=show_sql,
    )


@app.command("test", help="Run tests for a specific brick. Use --parallel for xdist parallel execution.")
def test(
    ctx: typer.Context,
    test_name: Annotated[
        list[str],
        typer.Argument(
            help="The name test file to launch (regular expression). Enter 'all' to launch all the tests."
        ),
    ],
    brick_name: Annotated[
        str,
        typer.Option(
            "--brick-name",
            help="Name of the brick to test. If not provided, use brick of current folder.",
        ),
    ]
    | None = None,
    parallel: Annotated[
        bool,
        typer.Option(
            "--parallel",
            help="Run tests in parallel via pytest-xdist. Each worker gets its own test DB schema.",
            is_flag=True,
        ),
    ] = False,
    workers: Annotated[
        str,
        typer.Option(
            "--workers",
            "-n",
            help="Number of parallel workers. 'auto' uses one per CPU. Only with --parallel.",
        ),
    ] = "auto",
    show_sql: ShowSqlAnnotation = False,
    durations: Annotated[
        int,
        typer.Option(
            "--durations",
            help="Print the N slowest tests after the run. Only with --parallel.",
        ),
    ] = 0,
):
    brick_dir: str
    if brick_name:
        brick_dir = BrickService.find_brick_folder(brick_name)
        typer.echo(f"Running tests for brick '{brick_dir}'")
    else:
        typer.echo("No brick dir provided. Using current directory.")
        brick_dir = CLIUtils.get_and_check_current_brick_dir()

    if parallel:
        pytest_args = [sys.executable, "-m", "pytest", "-n", workers]
        if durations > 0:
            pytest_args += [f"--durations={durations}"]

        if not (len(test_name) == 1 and test_name[0] in ("*", "all")):
            for name in test_name:
                filename = name if name.endswith(".py") else f"{name}.py"
                pytest_args += ["-k", os.path.splitext(filename)[0]]

        # Don't propagate sys.path via PYTHONPATH: it leaks into child subprocesses
        # spawned by tests (conda, pipenv, mamba) whose interpreters have different
        # stdlib versions, producing "SRE module mismatch" crashes. conftest.py at
        # the brick root adds src/ to sys.path for the master and every worker.
        os.chdir(brick_dir)
        os.execvp(pytest_args[0], pytest_args)

    AppManager.run_test(
        brick_dir=brick_dir,
        tests=test_name,
        log_level=CLIUtils.get_global_option_log_level(ctx),
        show_sql=show_sql,
    )


def _resolve_brick_dirs(brick_names: list[str]) -> list[str]:
    dirs: list[str] = []
    seen: set[str] = set()
    for name in brick_names:
        path = BrickService.find_brick_folder(name)
        if path not in seen:
            dirs.append(path)
            seen.add(path)
    return dirs


def _summarize_and_exit(results: list[tuple[str, int]]) -> None:
    typer.echo("\n=== test-all summary ===")
    any_failed = False
    for brick_dir, code in results:
        status = "PASS" if code == 0 else f"FAIL (exit {code})"
        typer.echo(f"  {os.path.basename(brick_dir)}: {status}")
        if code != 0:
            any_failed = True
    if any_failed:
        raise typer.Exit(code=1)


@app.command(
    "test-all",
    help="Run tests across multiple bricks sequentially. Each brick runs in a fresh subprocess.",
)
def test_all(
    ctx: typer.Context,
    brick_name: Annotated[
        list[str],
        typer.Option(
            "--brick-name",
            help="Brick to test. Repeat the flag for multiple bricks.",
        ),
    ],
    parallel: Annotated[
        bool,
        typer.Option(
            "--parallel",
            help="Use test-parallel (xdist) for each brick.",
            is_flag=True,
        ),
    ] = False,
    workers: Annotated[
        str,
        typer.Option(
            "--workers",
            "-n",
            help="Parallel workers per brick. Only with --parallel.",
        ),
    ] = "auto",
    durations: Annotated[
        int,
        typer.Option("--durations", help="Print the N slowest tests per brick."),
    ] = 0,
):
    brick_dirs = _resolve_brick_dirs(brick_name)
    log_level = CLIUtils.get_global_option_log_level(ctx)
    results: list[tuple[str, int]] = []

    for brick_dir in brick_dirs:
        typer.echo(f"\n=== Running tests for brick '{os.path.basename(brick_dir)}' ===")
        sub_cmd = ["gws", "--log-level", log_level, "server", "test", "all"]
        sub_cmd += ["--brick-name", os.path.basename(brick_dir)]
        if durations > 0:
            sub_cmd += ["--durations", str(durations)]
        if parallel:
            sub_cmd += ["--parallel", "-n", workers]
        proc = subprocess.run(sub_cmd, check=False)
        results.append((brick_dir, proc.returncode))

    _summarize_and_exit(results)


@app.command("run-scenario", help="Execute a specific scenario by ID")
def run_scenario(
    ctx: typer.Context,
    scenario_id: Annotated[str, typer.Option("--scenario-id", help="Id of the scenario to run.")],
    user_id: Annotated[
        str, typer.Option("--user-id", help="Id of the user that run the scenario.")
    ],
    main_setting_file_path: MainSettingFilePathAnnotation = CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH,
    show_sql: ShowSqlAnnotation = False,
    is_test: IsTestAnnotation = False,
):
    AppManager.run_scenario(
        main_setting_file_path=main_setting_file_path,
        scenario_id=scenario_id,
        user_id=user_id,
        log_level=CLIUtils.get_global_option_log_level(ctx),
        show_sql=show_sql,
        is_test=is_test,
    )


@app.command("run-process", help="Execute a specific process within a scenario")
def run_process(
    ctx: typer.Context,
    scenario_id: Annotated[str, typer.Option("--scenario-id", help="Id of the scenario to run.")],
    protocol_model_id: Annotated[
        str, typer.Option("--protocol-model-id", help="Id of the protocol model.")
    ],
    process_instance_name: Annotated[
        str, typer.Option("--process-instance-name", help="Name of the process instance.")
    ],
    user_id: Annotated[str, typer.Option("--user-id", help="Id of the user that run the process.")],
    main_setting_file_path: MainSettingFilePathAnnotation = CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH,
    show_sql: ShowSqlAnnotation = False,
    is_test: IsTestAnnotation = False,
):
    AppManager.run_process(
        main_setting_file_path=main_setting_file_path,
        scenario_id=scenario_id,
        protocol_model_id=protocol_model_id,
        process_instance_name=process_instance_name,
        user_id=user_id,
        log_level=CLIUtils.get_global_option_log_level(ctx),
        show_sql=show_sql,
        is_test=is_test,
    )
