import os
import sys
from typing import Annotated

import typer
from gws_core import BrickService
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.manage import AppManager
from gws_core.user.authorization_service import AuthorizationService

from gws_cli.utils.cli_utils import CLIUtils
from gws_cli.utils.test_runner import run_test_all

app = typer.Typer(
    help="Manage server operations - run server, execute tests, run scenarios and processes"
)


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


@app.command(
    "test", help="Run brick tests via pytest. Use --parallel for xdist parallel execution."
)
def test(
    ctx: typer.Context,
    test_name: Annotated[
        list[str],
        typer.Argument(help="Test file name(s) to launch. Enter 'all' to launch all the tests."),
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
    durations: Annotated[
        int,
        typer.Option("--durations", help="Print the N slowest tests after the run."),
    ] = 0,
    junit_xml: Annotated[
        str,
        typer.Option(
            "--junit-xml",
            help=(
                "Write a JUnit XML report to this path (consumed by `test-all` to assemble its "
                "JSON report)."
            ),
        ),
    ] = "",
):
    brick_dir: str
    if brick_name:
        brick_dir = BrickService.find_brick_folder(brick_name)
        typer.echo(f"Running tests for brick '{brick_dir}'")
    else:
        typer.echo("No brick dir provided. Using current directory.")
        brick_dir = CLIUtils.get_and_check_current_brick_dir()

    pytest_args = [sys.executable, "-m", "pytest"]
    if parallel:
        pytest_args += ["-n", workers]
    if durations > 0:
        pytest_args += [f"--durations={durations}"]
    if junit_xml:
        pytest_args += [f"--junitxml={junit_xml}"]

    if not (len(test_name) == 1 and test_name[0] in ("*", "all")):
        for name in test_name:
            filename = name if name.endswith(".py") else f"{name}.py"
            pytest_args += ["-k", os.path.splitext(filename)[0]]

    log_level = CLIUtils.get_global_option_log_level(ctx)
    if log_level:
        os.environ["GWS_TEST_LOG_LEVEL"] = log_level

    # If GWS_TEST_LOG_DIR isn't already set by a parent (e.g. test-all per-brick
    # subfolder), fall back to TEST_OUTPUT_DIR so direct `gws server test`
    # invocations also drop the log file alongside JUnit XML.
    if not os.environ.get("GWS_TEST_LOG_DIR") and os.environ.get("TEST_OUTPUT_DIR"):
        os.environ["GWS_TEST_LOG_DIR"] = os.environ["TEST_OUTPUT_DIR"]

    # Don't propagate sys.path via PYTHONPATH: it leaks into child subprocesses
    # spawned by tests (conda, pipenv, mamba) whose interpreters have different
    # stdlib versions, producing "SRE module mismatch" crashes. conftest.py at
    # the brick root adds src/ to sys.path for the master and every worker.
    os.chdir(brick_dir)
    os.execvp(pytest_args[0], pytest_args)


def _resolve_brick_dirs(brick_names: list[str]) -> list[str]:
    dirs: list[str] = []
    seen: set[str] = set()
    for name in brick_names:
        path = BrickService.find_brick_folder(name)
        if path not in seen:
            dirs.append(path)
            seen.add(path)
    return dirs


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
    output_dir: Annotated[
        str,
        typer.Option(
            "--output-dir",
            help=(
                "Folder to write per-brick test outputs (JUnit XML reports) into. "
                "Defaults to env var TEST_OUTPUT_DIR. If unset, outputs go to a "
                "temp dir and are deleted at the end."
            ),
        ),
    ] = "",
):
    results = run_test_all(
        brick_dirs=_resolve_brick_dirs(brick_name),
        log_level=CLIUtils.get_global_option_log_level(ctx),
        parallel=parallel,
        workers=workers,
        durations=durations,
        junit_dir=output_dir or os.environ.get("TEST_OUTPUT_DIR", ""),
    )
    if any(not r.is_success for r in results):
        raise typer.Exit(code=1)


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
