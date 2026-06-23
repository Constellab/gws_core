"""Read-only inspection of lab resources, intended for AI agents (e.g. Claude Code).

This is the resource counterpart of the ``db`` group: it loads resources by id,
searches them, reads their RFields, and renders their views — never mutating
anything. Design choices (shared with ``db_cli``):

- Errors print to stdout with a concrete next action so an agent can self-correct.
- Output is capped (``--limit``) to protect the agent's context window, and
  ``--format json`` is available for reliable parsing.

Typical flow for an agent that has no id yet:

    gws resource search --filter '[{"key":"name","operator":"CONTAINS","value":"robot"}]'
    gws resource info <id>
    gws resource fields <id>
    gws resource read <id> _data
    gws resource views <id>
    gws resource call-view <id> <view_name>
"""

import json
from typing import Annotated, Any

import typer
from gws_core.core.classes.search_builder import SearchOperator, SearchParams
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.manage import AppManager
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_service import ResourceService

from gws_cli.utils.agent_output import echo_json, fail, render_value
from gws_cli.utils.cli_utils import CLIUtils

SettingsPathOption = Annotated[
    str,
    typer.Option("--settings-path", help="Path to the main settings file (advanced)."),
]

DEFAULT_LIMIT = 20
DEFAULT_ATTR_LIMIT = 50

app = typer.Typer(
    help=(
        "Inspect lab resources (read-only; intended for AI agents).\n\n"
        "Find resources, read their RFields, and render their views:\n"
        "  gws resource search --filter '[{\"key\":\"name\",\"operator\":\"CONTAINS\",\"value\":\"x\"}]'\n"
        "  gws resource info <id>\n"
        "  gws resource fields <id>\n"
        "  gws resource read <id> _data\n"
        "  gws resource views <id>\n"
        "  gws resource call-view <id> <view_name>"
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


@app.command("search", help="Search resources with the advanced (operator-based) search.")
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
                "Common keys: name, id, data, created_at, created_by, origin, folder, "
                "is_archived. Special keys: resource_typing_name / resource_typing_names "
                "(matches the type AND its subtypes), generated_by_task, "
                'tags (value=[{"key":..,"value":..}]), column_tags (Table only). '
                "IMPORTANT defaults: only flagged resources are returned and children "
                'are excluded; add {"key":"include_not_flagged","value":true} and/or '
                '{"key":"include_children_resource","value":true} to widen the search.'
            ),
        ),
    ] = None,
    sort: Annotated[
        str | None,
        typer.Option(
            "--sort",
            help='JSON list of sort criteria: [{"key": <field>, "direction": "ASC"|"DESC"}]. '
            "Default: created_at DESC.",
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

    search_params = _build_search_params(filters, sort)

    _init_env(ctx, settings_path)

    try:
        paginator = ResourceService.search(search_params, page, limit)
    except BadRequestException as err:
        fail(
            f"search failed: {err}. Check that each filter 'key' is a valid resource "
            "field (see --help for the supported keys)."
        )

    _print_search_results(paginator, output_format)


def _build_search_params(filters: str | None, sort: str | None) -> SearchParams:
    """Parse the --filter / --sort JSON into a validated SearchParams."""
    params = SearchParams()

    for criteria in _parse_json_list(filters, "--filter"):
        if "key" not in criteria:
            fail(f"each --filter entry needs a 'key'; got {json.dumps(criteria)}.")
        operator_name = criteria.get("operator", "EQ")
        try:
            operator = SearchOperator[operator_name]
        except KeyError:
            valid = ", ".join(op.name for op in SearchOperator)
            fail(f"unknown operator '{operator_name}'. Valid operators: {valid}.")
        params.add_filter_criteria(criteria["key"], operator, criteria.get("value"))

    sort_criteria = _parse_json_list(sort, "--sort")
    if sort_criteria:
        params.sortsCriteria = sort_criteria

    return params


def _parse_json_list(raw: str | None, option_name: str) -> list[dict]:
    """Parse a JSON option that must decode to a list of objects (empty if None)."""
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as err:
        fail(f"{option_name} is not valid JSON: {err}.")
    if not isinstance(parsed, list):
        fail(f"{option_name} must be a JSON list, got {type(parsed).__name__}.")
    return parsed


def _print_search_results(paginator: Any, output_format: str) -> None:
    rows = [
        {
            "id": rm.id,
            "name": rm.name,
            "typing_name": rm.resource_typing_name,
            "created_at": rm.created_at,
            "flagged": rm.flagged,
        }
        for rm in paginator.results
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
        typer.echo("No resources matched. Note: by default only flagged resources are returned; ")
        typer.echo('add {"key":"include_not_flagged","value":true} to --filter to widen.')
        return

    for row in rows:
        flag = "flagged" if row["flagged"] else "-"
        typer.echo(f"{row['id']}  {row['name']}  [{row['typing_name']}]  {row['created_at']}  {flag}")
    typer.echo(
        f"\nPage {info.page} of {info.total_number_of_pages} "
        f"({info.total_number_of_items} item(s) total)."
    )


def _load_resource_model(resource_id: str) -> ResourceModel:
    resource_model = ResourceModel.get_by_id(resource_id)
    if resource_model is None:
        fail(
            f"no resource found with id '{resource_id}'. "
            "Find ids with 'gws resource search'."
        )
    return resource_model


@app.command("info", help="Show a resource's metadata (no content load).")
def info(
    ctx: typer.Context,
    resource_id: Annotated[str, typer.Argument(help="The id of the resource.")],
    settings_path: SettingsPathOption = CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH,
):
    _init_env(ctx, settings_path)
    resource_model = _load_resource_model(resource_id)
    echo_json(resource_model.to_dto().to_json_dict())


@app.command("fields", help="List a resource's RFields (its declared, persisted fields).")
def fields(
    ctx: typer.Context,
    resource_id: Annotated[str, typer.Argument(help="The id of the resource.")],
    settings_path: SettingsPathOption = CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH,
):
    _init_env(ctx, settings_path)
    resource_model = _load_resource_model(resource_id)
    try:
        loaded = resource_model.get_resource()
    except Exception as err:
        fail(f"could not load the resource content: {err}.")

    typer.echo(
        f"Resource '{resource_model.name}' "
        f"(type: {type(loaded).__name__}, typing: {resource_model.resource_typing_name})\n"
    )

    r_fields = type(loaded).__get_resource_r_fields__()
    if not r_fields:
        typer.echo("This resource declares no RFields.")
        return

    typer.echo("Available RFields (pass one or more names to 'gws resource read'):\n")
    for name in sorted(r_fields):
        field_type = type(r_fields[name]).__name__
        # Resolve the current value type (e.g. DataFrameRField -> DataFrame).
        try:
            value_type = type(getattr(loaded, name)).__name__
        except Exception:
            value_type = "?"
        typer.echo(f"  {name} ({field_type}) -> {value_type}")


@app.command("read", help="Print one or more RFields of a resource (loads the content).")
def read(
    ctx: typer.Context,
    resource_id: Annotated[str, typer.Argument(help="The id of the resource.")],
    attributes: Annotated[
        list[str],
        typer.Argument(
            help="RField name(s) to read, e.g. '_data'. Must be RFields "
            "(run 'gws resource fields <id>' to list them).",
        ),
    ],
    limit: Annotated[
        int,
        typer.Option(
            "--limit",
            help="Max rows (for DataFrame/Series RFields) to print, protecting the "
            f"agent context window. Default: {DEFAULT_ATTR_LIMIT}. Use 0 for no limit.",
        ),
    ] = DEFAULT_ATTR_LIMIT,
    settings_path: SettingsPathOption = CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH,
):
    _init_env(ctx, settings_path)
    resource_model = _load_resource_model(resource_id)
    try:
        loaded = resource_model.get_resource()
    except Exception as err:
        fail(f"could not load the resource content: {err}.")

    r_fields = type(loaded).__get_resource_r_fields__()
    for name in attributes:
        if name not in r_fields:
            valid = ", ".join(sorted(r_fields)) or "(none)"
            fail(
                f"'{name}' is not an RField of resource '{resource_model.name}' "
                f"(type: {type(loaded).__name__}, "
                f"typing: {resource_model.resource_typing_name}). "
                f"Valid RFields: {valid}. Run 'gws resource fields {resource_id}' to list them."
            )
        try:
            value = getattr(loaded, name)
        except Exception as err:
            value = f"<error reading RField: {err}>"
        typer.echo(f"=== {name} ({type(value).__name__}) ===")
        typer.echo(render_value(value, limit))
        typer.echo("")


@app.command("views", help="List the views available for a resource.")
def views(
    ctx: typer.Context,
    resource_id: Annotated[str, typer.Argument(help="The id of the resource.")],
    settings_path: SettingsPathOption = CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH,
):
    _init_env(ctx, settings_path)
    resource_model = _load_resource_model(resource_id)
    view_metas = ResourceService.get_views_of_resource(resource_model.resource_typing_name)

    if not view_metas:
        typer.echo("This resource type declares no views.")
        return

    typer.echo("Available views (pass a name to 'gws resource call-view'):\n")
    for meta in view_metas:
        dto = meta.to_dto()
        default = " (default)" if dto.default_view else ""
        typer.echo(f"  {dto.method_name}{default} - {dto.human_name} [{dto.view_type}]")
        if dto.short_description:
            typer.echo(f"      {dto.short_description}")


@app.command("call-view", help="Render a resource's view as JSON.")
def call_view(
    ctx: typer.Context,
    resource_id: Annotated[str, typer.Argument(help="The id of the resource.")],
    view_name: Annotated[
        str,
        typer.Argument(help="The view method name (see 'gws resource views <id>')."),
    ],
    config: Annotated[
        str | None,
        typer.Option("--config", help="JSON object of view config values. Default: {}."),
    ] = None,
    settings_path: SettingsPathOption = CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH,
):
    config_values: dict = {}
    if config:
        try:
            config_values = json.loads(config)
        except json.JSONDecodeError as err:
            fail(f"--config is not valid JSON: {err}.")
        if not isinstance(config_values, dict):
            fail("--config must be a JSON object.")

    _init_env(ctx, settings_path)
    # Ensure the resource exists first, for a clearer error than the view runner's.
    _load_resource_model(resource_id)

    try:
        result = ResourceService.get_and_call_view_on_resource_model(
            resource_id, view_name, config_values, save_view_config=False
        )
    except BadRequestException as err:
        fail(f"could not call view '{view_name}': {err}. List views with 'gws resource views {resource_id}'.")

    echo_json(result.to_dto().to_json_dict())
