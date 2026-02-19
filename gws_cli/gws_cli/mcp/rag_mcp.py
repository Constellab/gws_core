import json
import os
import uuid

from gws_core.community.community_service import CommunityService
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from mcp.server.fastmcp import FastMCP

TMP_DIR = "/lab/user/tmp"

mcp = FastMCP(
    "data-platform",
    instructions=(
        "This server provides access to the Constellab platform tools. "
        "Use the ask_platform tool BEFORE writing code when you have "
        "any question about Constellab, its Python library (gws_core), "
        "its APIs, conventions, or best practices. "
        "Use the get_documentation tool to retrieve the full content "
        "of a Constellab documentation page by its ID (UUID). "
        "The documentation is returned as JSON in EditorJs rich text format."
    ),
)

# Store the session ID to maintain conversation context across calls
_state: dict = {"session_id": None}


@mcp.tool(
    name="ask_platform",
    title="Constellab Chat Expert",
    description=(
        "Ask a question to the Constellab Chat Expert.\n\n"
        "This is a RAG-powered assistant that can answer:\n"
        "- Product questions about the Constellab platform (features, concepts, workflows)\n"
        "- Technical questions about developing on the platform (tasks, resources, protocols)\n"
        "- Questions about the gws_core library (classes, methods, patterns, best practices)\n"
        "- API usage, conventions, and coding guidelines\n\n"
        "Use this tool BEFORE writing code if you have any doubt about "
        "how something works on Constellab."
    ),
)
def ask_platform(question: str) -> str:
    """Ask a question to the Constellab Chat Expert."""

    try:
        result = CommunityService.ask_ragflow_chatbot(question, _state["session_id"])
    except Exception as e:
        return f"Error: {e}"

    # Persist the session ID for follow-up questions
    if result.session_id:
        _state["session_id"] = result.session_id

    return result.answer


@mcp.tool(
    name="get_documentation",
    title="Get Documentation Page",
    description=(
        "Retrieve a Constellab documentation page by its ID.\n\n"
        "Writes the documentation content as a JSON file (EditorJs rich text format) "
        "to /lab/user/tmp and returns the file path. "
        "The JSON includes a 'blocks' array, "
        "where each block has a 'type' (header, paragraph, code, list, table) "
        "and associated 'data'. Read the returned file to access the content.\n\n"
        "Args:\n"
        "  documentation_id: UUID of the documentation page to retrieve."
    ),
)
def get_documentation(documentation_id: str) -> str:
    """Retrieve a Constellab documentation page by its ID."""

    try:
        doc = CommunityService.get_documentation(documentation_id)
    except Exception as e:
        return f"Error: {e}"

    os.makedirs(TMP_DIR, exist_ok=True)
    filename = f"doc_{documentation_id}_{uuid.uuid4().hex[:8]}.json"
    filepath = os.path.join(TMP_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(doc.content.to_json_dict(), f, ensure_ascii=False, indent=2)

    return filepath


@mcp.tool(
    name="update_documentation",
    title="Update Documentation Page",
    description=(
        "Update the content of a Constellab documentation page.\n\n"
        "Reads a JSON file (EditorJs rich text format) from the given path "
        "and uploads it as the new content for the specified documentation page.\n\n"
        "Args:\n"
        "  json_file_path: Absolute path to the JSON file containing the new content.\n"
        "  documentation_id: UUID of the documentation page to update."
    ),
)
def update_documentation(json_file_path: str, documentation_id: str) -> bool:
    """Update the content of a Constellab documentation page."""
    try:
        with open(json_file_path, encoding="utf-8") as f:
            content_json = json.load(f)
    except FileNotFoundError:
        return False
    except json.JSONDecodeError:
        return False

    content = RichTextDTO.from_json(content_json)

    try:
        CommunityService.update_documentation_content(documentation_id, content)
    except Exception:
        return False

    return True


mcp.run(transport="stdio")
