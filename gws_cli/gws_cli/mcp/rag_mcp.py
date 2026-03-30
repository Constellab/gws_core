from gws_cli.utils.gws_core_loader import load_gws_core

load_gws_core()

from gws_core.community.community_user_service import CommunityUserApiService
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
        community_service = CommunityUserApiService()
        result = community_service.ask_ragflow_chatbot(question, _state["session_id"])
    except Exception as e:
        return f"Error: {e}"

    # Persist the session ID for follow-up questions
    if result.session_id:
        _state["session_id"] = result.session_id

    return result.answer


mcp.run(transport="stdio")
