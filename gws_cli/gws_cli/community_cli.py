import json
from typing import Annotated

import typer
from gws_core.impl.rich_text.rich_text_types import RichTextDTO

from .utils.community_cli_service import CommunityCliService

app = typer.Typer(help="Community commands (documentation, chatbot)")


@app.command("login", help="Login to the community platform")
def login(
    jwt_token: Annotated[str, typer.Argument(help="The JWT token to authenticate with.")],
):
    CommunityCliService.save_credentials(jwt_token)
    typer.echo("Login successful. Credentials saved.")


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
    result = CommunityCliService.get_community_service().update_documentation_content(
        documentation_id, content
    )
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
    with open(output_file_path, "w", encoding="utf-8") as f:
        json.dump(result.to_json_dict(), f, indent=2, ensure_ascii=False)

    typer.echo(f"Documentation '{result.title}' written to '{output_file_path}'.")
