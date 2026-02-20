import os


def init_gws_core():
    from gws_core_loader import load_gws_core

    load_gws_core()


init_gws_core()

from dataclasses import dataclass

from community_cli_service import CommunityCliService
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextBlock
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "rich-text-editor",
    instructions=(
        "This server provides tools to manipulate Constellab documentation pages "
        "stored as EditorJS rich text.\n"
        "Use load_remote_document to fetch a doc by its ID — it writes the markdown "
        "to a file and returns the path so you can read it.\n"
        "Use insert_blocks, update_block, move_block, and remove_block to make changes.\n"
        "Use upload_document to push the result back to the platform."
    ),
)

# Directory where markdown files are written
_MARKDOWN_DIR = "/lab/user/tmp"
os.makedirs(_MARKDOWN_DIR, exist_ok=True)


@dataclass
class _LoadedDocument:
    rich_text: RichText
    markdown_path: str


# In-memory document store keyed by documentation_id
_documents: dict[str, _LoadedDocument] = {}


def _get_document(documentation_id: str) -> _LoadedDocument:
    """Get a loaded document or raise an error."""
    if documentation_id not in _documents:
        raise ValueError(
            f"No document loaded for id '{documentation_id}'. Call load_remote_document first."
        )
    return _documents[documentation_id]


def _write_markdown(doc: _LoadedDocument) -> None:
    """Write the document's markdown (with block ID comments) to its file."""
    rich_text = doc.rich_text
    markdown = rich_text.to_markdown(include_block_comments=True)
    blocks = rich_text.get_blocks()
    header = f"> {len(blocks)} blocks\n\n"
    with open(doc.markdown_path, "w", encoding="utf-8") as f:
        f.write(header + markdown)


# ==================== Document lifecycle ====================


@mcp.tool(
    name="load_remote_document",
    title="Load Remote Documentation",
    description=(
        "Load a Constellab documentation page by its ID.\n\n"
        "If the document is already loaded in memory, returns the markdown file path "
        "directly without fetching from the platform.\n"
        "Otherwise fetches from the platform, loads into memory, writes the markdown "
        "(with block ID comments) to a file, and returns the file path.\n\n"
        "Args:\n"
        "  documentation_id: UUID of the documentation page to retrieve."
    ),
)
def load_remote_document(documentation_id: str) -> str:
    """Load a documentation page. Returns cached markdown if already loaded."""
    if documentation_id in _documents:
        doc = _documents[documentation_id]
        _write_markdown(doc)
        blocks = doc.rich_text.get_blocks()
        return f"Document already loaded ({len(blocks)} blocks). Markdown written to: {doc.markdown_path}"

    community_service = CommunityCliService.get_community_service()
    result = community_service.get_documentation(documentation_id)

    rich_text = RichText(result.content)
    file_path = os.path.join(_MARKDOWN_DIR, f"{documentation_id}.md")
    doc = _LoadedDocument(rich_text=rich_text, markdown_path=file_path)
    _documents[documentation_id] = doc

    _write_markdown(doc)

    blocks = rich_text.get_blocks()
    return (
        f"Document '{result.title}' loaded ({len(blocks)} blocks). Markdown written to: {file_path}"
    )


@mcp.tool(
    name="upload_document",
    title="Upload Document to Platform",
    description=(
        "Upload the in-memory document back to the Constellab platform.\n\n"
        "This overwrites the remote documentation page content with the current "
        "in-memory state of the document.\n\n"
        "Args:\n"
        "  documentation_id: UUID of the documentation page (must have been loaded first)."
    ),
)
def upload_document(documentation_id: str) -> str:
    """Upload the document to the platform."""
    doc = _get_document(documentation_id)
    community_service = CommunityCliService.get_community_service()
    result = community_service.update_documentation_content(documentation_id, doc.rich_text.to_dto())
    return f"Uploaded '{result.title}' (id={result.id}) — {len(doc.rich_text.get_blocks())} blocks"


# ==================== Block tools ====================


@mcp.tool(
    name="insert_blocks",
    title="Insert Blocks After ID",
    description=(
        "Insert one or more blocks after the block with the given ID.\n\n"
        "Each block in the list must have:\n"
        "  - type: The block type string (e.g. 'paragraph', 'header', 'list', 'table', "
        "'code', 'hint', 'quote', 'video', 'iframe', 'html', 'formula').\n"
        "  - data: The block data dict matching the type schema.\n\n"
        "Common data schemas:\n"
        '  - paragraph: {"text": "..."}\n'
        "    Text supports HTML: <b>, <i>, <u>, <code>, <a href=''>.\n"
        '  - header: {"text": "...", "level": 2|3|4}\n'
        '  - list: {"style": "ordered"|"unordered", "items": [\n'
        '      {"content": "Item text with <b>bold</b>", "meta": {}, "items": []},\n'
        '      {"content": "Second item", "meta": {}, "items": [\n'
        '        {"content": "Nested item", "meta": {}, "items": []}\n'
        "      ]}\n"
        "    ]}\n"
        "    style is 'ordered' or 'unordered'. Nested items go in the inner items array.\n"
        "    Item content supports the same HTML as paragraphs.\n"
        '  - table: {"withHeadings": true|false, "stretched": false, "content": [\n'
        '      ["Column 1", "Column 2", "Column 3"],\n'
        '      ["Value with <b>bold</b>", "Description<br>Second line", "Default"]\n'
        "    ]}\n"
        "    When withHeadings is true, the first row is the header row.\n"
        "    Cell content supports the same HTML as paragraphs.\n"
        '  - code: {"code": "...", "language": "python"}\n'
        '  - hint: {"content": "...", "hintType": "info"|"warning"|"science"}\n'
        '  - quote: {"text": "...", "caption": "..."}\n'
        '  - video: {"url": "...", "caption": "..."}\n\n'
        "Args:\n"
        "  documentation_id: ID of the loaded document.\n"
        "  after_block_id: Insert after this block ID.\n"
        "  blocks: List of {type, data} dicts to insert in order."
    ),
)
def insert_blocks(
    documentation_id: str,
    after_block_id: str,
    blocks: list[dict],
) -> str:
    """Insert one or more blocks after the given block ID."""
    rich_text = _get_document(documentation_id).rich_text

    new_blocks: list[RichTextBlock] = []
    for block_def in blocks:
        block_type = block_def.get("type")
        block_data = block_def.get("data")
        if not block_type or block_data is None:
            raise ValueError("Each block must have 'type' and 'data' keys.")
        block_id = rich_text.generate_id()
        new_blocks.append(RichTextBlock(id=block_id, type=block_type, data=block_data))

    rich_text.insert_multiple_blocks_after_id(after_block_id, new_blocks)

    ids = [b.id for b in new_blocks]
    return f"Inserted {len(new_blocks)} block(s) after {after_block_id}: {ids}"


@mcp.tool(
    name="update_block",
    title="Update Block Data",
    description=(
        "Update the data of an existing block by ID. "
        "The block's id and type are preserved — only the data changes.\n\n"
        "Args:\n"
        "  documentation_id: ID of the loaded document.\n"
        "  block_id: ID of the block to update.\n"
        "  data: New data dict for the block (must match the block's type schema)."
    ),
)
def update_block(documentation_id: str, block_id: str, data: dict) -> str:
    """Update a block's data while preserving its id and type."""
    rich_text = _get_document(documentation_id).rich_text
    block = rich_text.get_block_by_id(block_id)
    if block is None:
        raise ValueError(f"Block with id '{block_id}' not found")

    new_block = RichTextBlock(id=block.id, type=block.type, data=data)
    rich_text.replace_block_by_id(block_id, new_block)

    return f"Updated block {block_id} (type={block.type})"


@mcp.tool(
    name="remove_block",
    title="Remove Block",
    description=(
        "Remove a block from the document by its ID.\n\n"
        "Args:\n"
        "  documentation_id: ID of the loaded document.\n"
        "  block_id: ID of the block to remove."
    ),
)
def remove_block(documentation_id: str, block_id: str) -> str:
    """Remove a block by ID."""
    rich_text = _get_document(documentation_id).rich_text
    block = rich_text.get_block_by_id(block_id)
    if block is None:
        raise ValueError(f"Block with id '{block_id}' not found")

    rich_text.remove_block_by_id(block_id)
    return f"Removed block {block_id} (type={block.type})"


@mcp.tool(
    name="move_block",
    title="Move Block",
    description=(
        "Move a block to a new position in the document.\n\n"
        "Args:\n"
        "  documentation_id: ID of the loaded document.\n"
        "  block_id: ID of the block to move.\n"
        "  after_block_id: Place the block after this block ID. "
        "If omitted, move to the beginning of the document."
    ),
)
def move_block(documentation_id: str, block_id: str, after_block_id: str | None = None) -> str:
    """Move a block to after another block."""
    rich_text = _get_document(documentation_id).rich_text
    rich_text.move_block(block_id, after_block_id)

    position = "beginning" if after_block_id is None else f"after {after_block_id}"
    return f"Moved block {block_id} to {position}"


mcp.run(transport="stdio")
