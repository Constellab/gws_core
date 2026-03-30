import json
from datetime import datetime, timezone
from typing import Annotated

import typer
from gws_core.community.community_auth_service import CommunityAuthService
from gws_core.community.community_credential_service import CommunityCredentialService
from gws_core.community.community_user_service import CommunityUserApiService, TokenExpiredError
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextDTO

app = typer.Typer(help="Community commands (documentation, chatbot)")


@app.command("login", help="Authenticate with the Community platform via browser")
def login(
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Re-authenticate even if already logged in."),
    ] = False,
):
    try:
        CommunityAuthService.run_login_flow(force=force)
    except KeyboardInterrupt:
        typer.echo("\nLogin cancelled.")
        raise typer.Exit(0)


@app.command("logout", help="Remove stored authentication credentials")
def logout(
    all_domains: Annotated[
        bool,
        typer.Option("--all", help="Remove credentials for all domains."),
    ] = False,
):
    if all_domains:
        domains = CommunityCredentialService.get_stored_domains()
        if not domains:
            typer.echo("No stored credentials found.")
            return
        CommunityCredentialService.delete_all_credentials()
        typer.echo(f"Logged out from all domains ({len(domains)}).")
        return

    if (
        not CommunityCredentialService.has_credentials()
        and not CommunityCredentialService.is_token_expired()
    ):
        typer.echo("You are not logged in.")
        return

    domain = CommunityCredentialService.get_current_api_domain()
    CommunityCredentialService.delete_credentials()
    typer.echo(f"You have been logged out from {domain}.")


@app.command("status", help="Show current authentication status")
def status():
    domain = CommunityCredentialService.get_current_api_domain()
    access_token, expires_at = CommunityCredentialService.load_credentials(domain)

    typer.echo(f"Domain: {domain}")

    if access_token is None:
        typer.echo("Status: Not logged in")
        return

    if expires_at is not None:
        expires_dt = datetime.fromtimestamp(expires_at, tz=timezone.utc)
        if datetime.now(tz=timezone.utc) >= expires_dt:
            typer.echo(
                f"Status: Expired (expired on {expires_dt.strftime('%Y-%m-%d %H:%M:%S UTC')})"
            )
        else:
            typer.echo(
                f"Status: Logged in (expires on {expires_dt.strftime('%Y-%m-%d %H:%M:%S UTC')})"
            )
    else:
        typer.echo("Status: Logged in (no expiration info)")

    # Show other stored domains
    all_domains = CommunityCredentialService.get_stored_domains()
    other_domains = [d for d in all_domains if d != domain]
    if other_domains:
        typer.echo(f"\nOther stored domains: {', '.join(other_domains)}")


@app.command("ask-chatbot", help="Ask a question to the Ragflow chatbot")
def ask_ragflow_chatbot(
    message: Annotated[str, typer.Argument(help="The question to ask the chatbot.")],
    session_id: Annotated[
        str, typer.Option("--session-id", help="Optional session ID to continue a conversation.")
    ]
    | None = None,
):
    result = CommunityUserApiService().ask_ragflow_chatbot(
        message, session_id=session_id
    )
    typer.echo(f"Answer: {result.answer}")
    typer.echo(f"Session ID: {result.session_id}")
    # if result.references:
    #     typer.echo(f"References: {json.dumps(result.references, indent=2)}")


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
    try:
        result = CommunityUserApiService(
            requires_authentication=True
        ).update_documentation_content(documentation_id, content)
    except TokenExpiredError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e
    typer.echo(f"Documentation '{result.title}' (id={result.id}) updated successfully.")


@app.command(
    "get-doc", help="Retrieve a documentation page and write it to a file in markdown format"
)
def get_documentation(
    documentation_id: Annotated[
        str, typer.Argument(help="ID of the documentation page to retrieve.")
    ],
    output_file_path: Annotated[
        str,
        typer.Argument(
            help="Path to the output file where the documentation markdown will be written."
        ),
    ],
):
    result = CommunityUserApiService().get_documentation(documentation_id)

    rich_text = RichText(result.content)
    markdown = rich_text.to_markdown(include_block_comments=True)

    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    typer.echo(f"Documentation '{result.title}' written to '{output_file_path}'.")
