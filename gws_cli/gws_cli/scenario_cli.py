"""Inspect and control lab scenarios from the CLI, intended for AI agents.

Most commands are read-only (search, info, running, resources, error). Two
commands — ``start`` and ``stop`` — mutate scenario state and therefore require
the ``--yes`` flag to run.

Conventions (shared with the ``db`` and ``resource`` groups):

- Errors print to stdout with a concrete next action so an agent can self-correct.
- Output is capped (``--limit``) to protect the agent's context window, and
  ``--format json`` is available for reliable parsing.

Typical flow:

    gws scenario search --filter '[{"key":"status","operator":"EQ","value":"ERROR"}]'
    gws scenario info <id>
    gws scenario error <id>
    gws scenario resources <id>
"""

from typing import Annotated, Any

import typer
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.manage import AppManager
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.resource.resource_service import ResourceService
from gws_core.scenario.queue.queue_service import QueueService
from gws_core.scenario.scenario_run_service import ScenarioRunService
from gws_core.scenario.scenario_service import ScenarioService

from gws_cli.utils.agent_output import build_search_params, echo_json, fail
from gws_cli.utils.cli_utils import CLIUtils

SettingsPathOption = Annotated[
    str,
    typer.Option("--settings-path", help="Path to the main settings file (advanced)."),
]

DEFAULT_LIMIT = 20

app = typer.Typer(
    help=(
        "Inspect and control lab scenarios (intended for AI agents).\n\n"
        "Read-only: search, info, running, protocol, resources, error.\n"
        "State-changing (require --yes): start, stop.\n"
        "  gws scenario search --filter '[{\"key\":\"status\",\"operator\":\"EQ\",\"value\":\"ERROR\"}]'\n"
        "  gws scenario info <id>\n"
        "  gws scenario error <id>\n"
        "  gws scenario resources <id>"
    )
)


def _init_env(ctx: typer.Context, settings_path: str) -> None:
    """Initialize the lab environment + db (loads bricks, connects every db)."""
    try:
        AppManager.init_gws_env_and_db(
            settings_path, log_level=CLIUtils.get_global_option_log_level(ctx)
        )
    except Exception as err:
        fail(
            f"could not initialize the lab environment: {err}. "
            "Is the lab db reachable? Try 'gws server run' first."
        )


def _check_format(output_format: str) -> None:
    if output_format not in ("table", "json"):
        fail("--format must be 'table' or 'json'.")


def _load_scenario(scenario_id: str) -> Any:
    try:
        return ScenarioService.get_by_id_and_check(scenario_id)
    except Exception:
        fail(
            f"no scenario found with id '{scenario_id}'. Find ids with 'gws scenario search'."
        )


@app.command("search", help="Search scenarios with the advanced (operator-based) search.")
def search(
    ctx: typer.Context,
    filters: Annotated[
        str | None,
        typer.Option(
            "--filter",
            help=(
                "JSON list of filter criteria: "
                '[{"key": <field>, "operator": <OP>, "value": <val>}]. '
                "Operators: EQ NEQ LT LE GT GE CONTAINS IN NOT_IN NULL NOT_NULL "
                "START_WITH END_WITH MATCH BETWEEN. "
                "Common keys: title, status (DRAFT/IN_QUEUE/RUNNING/SUCCESS/ERROR/"
                "PARTIALLY_RUN), is_validated, is_archived, created_at, folder. "
                "Special keys: process_typing_name (scenarios containing that task type), "
                'tags (value=[{"key":..,"value":..}]).'
            ),
        ),
    ] = None,
    sort: Annotated[
        str | None,
        typer.Option(
            "--sort",
            help='JSON list of sort criteria: [{"key": <field>, "direction": "ASC"|"DESC"}].',
        ),
    ] = None,
    page: Annotated[
        int,
        typer.Option("--page", help="Page number (0-based). Default: 0."),
    ] = 0,
    limit: Annotated[
        int,
        typer.Option("--limit", help=f"Items per page. Default: {DEFAULT_LIMIT}."),
    ] = DEFAULT_LIMIT,
    output_format: Annotated[
        str,
        typer.Option("--format", help="Output format: 'table' (default) or 'json'."),
    ] = "table",
    settings_path: SettingsPathOption = CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH,
):
    _check_format(output_format)
    search_params = build_search_params(filters, sort)

    _init_env(ctx, settings_path)

    try:
        paginator = ScenarioService.search(search_params, page, limit)
    except BadRequestException as err:
        fail(
            f"search failed: {err}. Check that each filter 'key' is a valid scenario "
            "field (see --help for the supported keys)."
        )

    _print_search_results(paginator, output_format)


def _print_search_results(paginator: Any, output_format: str) -> None:
    rows = [
        {
            "id": sc.id,
            "title": sc.title,
            "status": sc.status.value if hasattr(sc.status, "value") else sc.status,
            "is_validated": sc.is_validated,
            "is_archived": sc.is_archived,
            "created_at": sc.created_at,
        }
        for sc in paginator.results
    ]
    info = paginator.page_info

    if output_format == "json":
        echo_json(
            {
                "page": info.page,
                "total_pages": info.total_number_of_pages,
                "total_items": info.total_number_of_items,
                "results": rows,
            }
        )
        return

    if not rows:
        typer.echo("No scenarios matched.")
        return

    for row in rows:
        flags = []
        if row["is_validated"]:
            flags.append("validated")
        if row["is_archived"]:
            flags.append("archived")
        flag_str = f"  ({', '.join(flags)})" if flags else ""
        typer.echo(f"{row['id']}  [{row['status']}]  {row['title']}  {row['created_at']}{flag_str}")
    typer.echo(
        f"\nPage {info.page} of {info.total_number_of_pages} "
        f"({info.total_number_of_items} item(s) total)."
    )


@app.command("info", help="Show a scenario's metadata.")
def info(
    ctx: typer.Context,
    scenario_id: Annotated[str, typer.Argument(help="The id of the scenario.")],
    settings_path: SettingsPathOption = CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH,
):
    _init_env(ctx, settings_path)
    scenario = _load_scenario(scenario_id)
    echo_json(scenario.to_dto().to_json_dict())


@app.command("running", help="List the currently running scenarios with their progress.")
def running(
    ctx: typer.Context,
    output_format: Annotated[
        str,
        typer.Option("--format", help="Output format: 'table' (default) or 'json'."),
    ] = "table",
    settings_path: SettingsPathOption = CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH,
):
    _check_format(output_format)
    _init_env(ctx, settings_path)
    scenarios = ScenarioService.get_running_scenarios()

    if output_format == "json":
        echo_json([sc.to_json_dict() for sc in scenarios])
        return

    if not scenarios:
        typer.echo("No scenario is currently running.")
        return

    for sc in scenarios:
        typer.echo(f"{sc.id}  {sc.title}")
        for task in sc.running_tasks:
            progress = f"{task.progression:.0f}%" if task.progression is not None else "?"
            typer.echo(f"    [{progress}] {task.title} - {task.last_message or ''}")


@app.command("error", help="Show the failure info of a scenario (if it errored).")
def error(
    ctx: typer.Context,
    scenario_id: Annotated[str, typer.Argument(help="The id of the scenario.")],
    settings_path: SettingsPathOption = CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH,
):
    _init_env(ctx, settings_path)
    scenario = _load_scenario(scenario_id)
    error_info = scenario.get_error_info()

    if error_info is None:
        status = scenario.status.value if hasattr(scenario.status, "value") else scenario.status
        typer.echo(f"Scenario '{scenario.title}' has no error info (status: {status}).")
        return

    echo_json(error_info.to_json_dict())


@app.command("protocol", help="Print a scenario's protocol as JSON (the full process graph).")
def protocol(
    ctx: typer.Context,
    scenario_id: Annotated[str, typer.Argument(help="The id of the scenario.")],
    settings_path: SettingsPathOption = CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH,
):
    _init_env(ctx, settings_path)
    scenario = _load_scenario(scenario_id)
    # Same path as the "/protocol/{id_}" GET endpoint: resolve the protocol by id
    # via ProtocolService and serialize with to_protocol_dto().
    try:
        protocol_model = ProtocolService.get_by_id_and_check(scenario.protocol_model.id)
        protocol_dto = protocol_model.to_protocol_dto()
    except Exception as err:
        fail(f"could not build the protocol: {err}.")
    echo_json(protocol_dto.to_json_dict())


@app.command("resources", help="List the resources a scenario produced and consumed.")
def resources(
    ctx: typer.Context,
    scenario_id: Annotated[str, typer.Argument(help="The id of the scenario.")],
    output_format: Annotated[
        str,
        typer.Option("--format", help="Output format: 'table' (default) or 'json'."),
    ] = "table",
    settings_path: SettingsPathOption = CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH,
):
    _check_format(output_format)
    _init_env(ctx, settings_path)
    # Validate the scenario exists for a clear error.
    _load_scenario(scenario_id)

    resource_models = ResourceService.get_scenarios_resources([scenario_id])
    rows = [
        {
            "id": rm.id,
            "name": rm.name,
            "typing_name": rm.resource_typing_name,
            "flagged": rm.flagged,
        }
        for rm in resource_models
    ]

    if output_format == "json":
        echo_json(rows)
        return

    if not rows:
        typer.echo("No resources found for this scenario.")
        return

    typer.echo("Resources used/produced by this scenario (inspect with 'gws resource'):\n")
    for row in rows:
        flag = "flagged" if row["flagged"] else "-"
        typer.echo(f"  {row['id']}  {row['name']}  [{row['typing_name']}]  {flag}")


def _require_yes(yes: bool, action: str) -> None:
    if not yes:
        fail(
            f"'{action}' changes scenario state and is not run by default. "
            "Re-run with --yes to confirm."
        )


@app.command("start", help="Start a scenario (queues it for execution). Requires --yes.")
def start(
    ctx: typer.Context,
    scenario_id: Annotated[str, typer.Argument(help="The id of the scenario.")],
    yes: Annotated[
        bool,
        typer.Option("--yes", help="Confirm: actually start the scenario."),
    ] = False,
    settings_path: SettingsPathOption = CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH,
):
    _require_yes(yes, "start")
    _init_env(ctx, settings_path)
    _load_scenario(scenario_id)

    try:
        scenario = QueueService.add_scenario_to_queue(scenario_id=scenario_id)
    except Exception as err:
        fail(f"could not start scenario: {err}.")

    status = scenario.status.value if hasattr(scenario.status, "value") else scenario.status
    typer.echo(f"Scenario '{scenario.title}' queued (status: {status}).")


@app.command("stop", help="Stop a running scenario. Requires --yes.")
def stop(
    ctx: typer.Context,
    scenario_id: Annotated[str, typer.Argument(help="The id of the scenario.")],
    yes: Annotated[
        bool,
        typer.Option("--yes", help="Confirm: actually stop the scenario."),
    ] = False,
    settings_path: SettingsPathOption = CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH,
):
    _require_yes(yes, "stop")
    _init_env(ctx, settings_path)
    _load_scenario(scenario_id)

    try:
        scenario = ScenarioRunService.stop_scenario(scenario_id)
    except Exception as err:
        fail(f"could not stop scenario: {err}.")

    status = scenario.status.value if hasattr(scenario.status, "value") else scenario.status
    typer.echo(f"Scenario '{scenario.title}' stopped (status: {status}).")
