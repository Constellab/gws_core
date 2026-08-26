import json
from datetime import datetime, timezone
from typing import Annotated

import typer
from gws_core.community.community_dto import HnNode
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextDTO

from .utils.community_cli_service import CommunityCliService, TokenExpiredError

app = typer.Typer(help="Community commands (documentation, chatbot)")


@app.command("login", help="Authenticate with the Community platform via browser")
def login(
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Re-authenticate even if already logged in."),
    ] = False,
):
    try:
        CommunityCliService.run_login_flow(force=force)
    except KeyboardInterrupt:
        typer.echo("\nLogin cancelled.")
        raise typer.Exit(0) from None


@app.command("logout", help="Remove stored authentication credentials")
def logout(
    all_domains: Annotated[
        bool,
        typer.Option("--all", help="Remove credentials for all domains."),
    ] = False,
):
    if all_domains:
        domains = CommunityCliService.get_stored_domains()
        if not domains:
            typer.echo("No stored credentials found.")
            return
        CommunityCliService.delete_all_credentials()
        typer.echo(f"Logged out from all domains ({len(domains)}).")
        return

    if not CommunityCliService.has_credentials() and not CommunityCliService.is_token_expired():
        typer.echo("You are not logged in.")
        return

    domain = CommunityCliService._get_current_api_domain()
    CommunityCliService.delete_credentials()
    typer.echo(f"You have been logged out from {domain}.")


@app.command("status", help="Show current authentication status")
def status():
    domain = CommunityCliService._get_current_api_domain()
    access_token, expires_at = CommunityCliService.load_credentials(domain)

    typer.echo(f"Domain: {domain}")

    if access_token is None:
        typer.echo("Status: Not logged in")
        return

    if expires_at is not None:
        expires_dt = datetime.fromtimestamp(expires_at, tz=timezone.utc)
        if datetime.now(tz=timezone.utc) >= expires_dt:
            typer.echo(f"Status: Expired (expired on {expires_dt.strftime('%Y-%m-%d %H:%M:%S UTC')})")
        else:
            typer.echo(f"Status: Logged in (expires on {expires_dt.strftime('%Y-%m-%d %H:%M:%S UTC')})")
    else:
        typer.echo("Status: Logged in (no expiration info)")

    # Show other stored domains
    all_domains = CommunityCliService.get_stored_domains()
    other_domains = [d for d in all_domains if d != domain]
    if other_domains:
        typer.echo(f"\nOther stored domains: {', '.join(other_domains)}")


# Command to create a new folder in a folder
@app.command("create-folder", help="Create a new folder inside a folder")
def create_folder(
    folder_id: Annotated[
        str,
        typer.Argument(help="ID of the parent folder to create the folder in."),
    ],
    title: Annotated[
        str,
        typer.Argument(help="Title of the new folder."),
    ],
):
    try:
        result = CommunityCliService.get_community_service(
            requires_authentication=True
        ).create_folder(folder_id, title)
    except TokenExpiredError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e
    typer.echo(f"Folder '{result.get('title', title)}' created successfully (id={result.get('id')}).")


# Command to create a new empty documentation page in a folder
@app.command("create-doc", help="Create a new empty documentation page inside a folder")
def create_documentation(
    folder_id: Annotated[
        str,
        typer.Argument(help="ID of the folder to create the documentation page in."),
    ],
    title: Annotated[
        str,
        typer.Argument(help="Title of the new documentation page."),
    ],
):
    try:
        result = CommunityCliService.get_community_service(
            requires_authentication=True
        ).create_documentation(folder_id, title)
    except TokenExpiredError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e
    typer.echo(f"Documentation '{result.title}' created successfully (id={result.id}).")
    typer.echo(f"Push content to it with: gws community update-doc {result.id} <json_file_path>")


def _validate_rich_text_content(content: RichTextDTO) -> None:
    """Validate every block's data against its platform schema before uploading.

    ``RichTextDTO.from_json`` only validates the top-level envelope, not each block's
    ``data``: a block with a valid ``type`` but wrong ``data`` fields (e.g. a ``hint``
    using ``title``/``message`` instead of ``content``) parses fine here but fails to
    render, leaving an empty page. ``block.get_data()`` forces the per-block schema
    validation that rendering would, so we catch the bad block here rather than on the
    server. Exits with a message naming the offending block.
    """
    for index, block in enumerate(RichText(content).get_blocks()):
        try:
            block.get_data()
        except Exception as e:
            block_id = block.id or "<no id>"
            typer.echo(
                f"Error: block #{index} (id={block_id}, type={block.type}) is invalid "
                f"and would render as an empty page.\n{e}",
                err=True,
            )
            raise typer.Exit(1) from e


# Command to update a documentation's content from a JSON file
@app.command("update-doc", help="Update a documentation page content from a JSON file")
def update_documentation(
    documentation_id: Annotated[
        str, typer.Argument(help="ID of the documentation page to update.")
    ],
    json_file_path: Annotated[
        str,
        typer.Argument(
            help="Path to the JSON file containing the new content (RichTextDTO format)."
        ),
    ],
):
    with open(json_file_path, encoding="utf-8") as f:
        content_dict = json.load(f)

    content = RichTextDTO.from_json(content_dict)
    _validate_rich_text_content(content)
    try:
        result = CommunityCliService.get_community_service(
            requires_authentication=True
        ).update_documentation_content(documentation_id, content)
    except TokenExpiredError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e
    typer.echo(f"Documentation '{result.title}' (id={result.id}) updated successfully.")


@app.command("ask-chatbot", help="Ask a question to the Ragflow chatbot")
def ask_ragflow_chatbot(
    message: Annotated[str, typer.Argument(help="The question to ask the chatbot.")],
    session_id: Annotated[
        str, typer.Option("--session-id", help="Optional session ID to continue a conversation.")
    ]
    | None = None,
):
    result = CommunityCliService.get_community_service().ask_ragflow_chatbot(
        message, session_id=session_id
    )
    typer.echo(f"Answer: {result.answer}")
    typer.echo(f"Session ID: {result.session_id}")
    # if result.references:
    #     typer.echo(f"References: {json.dumps(result.references, indent=2)}")


@app.command("get-doc", help="Retrieve a documentation page and write it to a file")
def get_documentation(
    documentation_id: Annotated[
        str, typer.Argument(help="ID of the documentation page to retrieve.")
    ],
    output_file_path: Annotated[
        str,
        typer.Argument(
            help="Path to the output file where the documentation JSON will be written."
        ),
    ],
):
    result = CommunityCliService.get_community_service().get_documentation(documentation_id)

    rich_text = RichText(result.content)
    markdown = rich_text.to_markdown(include_block_comments=True)

    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    typer.echo(f"Documentation '{result.title}' written to '{output_file_path}'.")


def _print_hierarchy(node: HnNode, indent: int = 0) -> None:
    """Print a documentation hierarchy node and its children as an indented tree."""
    typer.echo(f"{'  ' * indent}{node.name or '<root>'} (id={node.id})")
    for child in node.children or []:
        _print_hierarchy(child, indent + 1)


@app.command("doc-hierarchy", help="Show the documentation hierarchy (tree) of a brick")
def documentation_hierarchy(
    brick_id: Annotated[
        str, typer.Argument(help="ID of the brick whose documentation hierarchy to retrieve.")
    ],
    brick_version: Annotated[
        str,
        typer.Option("--version", help="Brick version to retrieve the hierarchy for."),
    ] = "latest",
    output_format: Annotated[
        str, typer.Option("--format", help="Output format: 'text' (default) or 'json'.")
    ] = "text",
):
    result = CommunityCliService.get_community_service().get_documentation_hierarchy(
        brick_id, brick_version
    )

    if output_format == "json":
        typer.echo(json.dumps(result.to_json_dict(), indent=2))
    else:
        _print_hierarchy(result)
