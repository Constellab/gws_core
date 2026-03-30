import os
from dataclasses import dataclass

from gws_cli.utils.gws_core_loader import load_gws_core

load_gws_core()

from gws_core.community.community_user_service import CommunityUserApiService
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
        "Use get_block_data to inspect a block's raw JSON data before updating it.\n"
        "Use insert_blocks, update_block, move_block, remove_block, batch_operations, "
        "and replace_section to make changes.\n"
        "Use upload_document to push the result back to the platform.\n\n"
        "Prefer batch_operations over multiple individual calls when you need to "
        "update, insert, or remove several blocks at once.\n"
        "Use replace_section to rewrite an entire section (header + all its content "
        "blocks) in one call.\n"
        "Use get_block_data to fetch the exact data dict of complex blocks (tables, "
        "lists, etc.) before updating them — the markdown alone may not capture all fields."
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

    community_service = CommunityUserApiService(requires_authentication=True)
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
    community_service = CommunityUserApiService(requires_authentication=True)
    result = community_service.update_documentation_content(
        documentation_id, doc.rich_text.to_dto()
    )
    return f"Uploaded '{result.title}' (id={result.id}) — {len(doc.rich_text.get_blocks())} blocks"


# ==================== Block tools ====================


@mcp.tool(
    name="get_block_data",
    title="Get Block Data",
    description=(
        "Get the raw JSON data of a block by its ID.\n\n"
        "Use this before calling update_block on complex blocks (tables, lists, etc.) "
        "to get their exact data dict. This avoids guessing the structure from markdown.\n\n"
        "Args:\n"
        "  documentation_id: ID of the loaded document.\n"
        "  block_id: ID of the block to inspect."
    ),
)
def get_block_data(documentation_id: str, block_id: str) -> dict:
    """Return the block's type and data dict."""
    rich_text = _get_document(documentation_id).rich_text
    block = rich_text.get_block_by_id(block_id)
    if block is None:
        raise ValueError(f"Block with id '{block_id}' not found")
    return {"id": block.id, "type": block.type, "data": block.data}


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
        "  after_block_id: Insert after this block ID. "
        "If omitted or null, inserts at the beginning of the document.\n"
        "  blocks: List of {type, data} dicts to insert in order."
    ),
)
def insert_blocks(
    documentation_id: str,
    blocks: list[dict],
    after_block_id: str | None = None,
) -> str:
    """Insert one or more blocks after the given block ID, or at the beginning."""
    rich_text = _get_document(documentation_id).rich_text

    new_blocks: list[RichTextBlock] = []
    for block_def in blocks:
        block_type = block_def.get("type")
        block_data = block_def.get("data")
        if not block_type or block_data is None:
            raise ValueError("Each block must have 'type' and 'data' keys.")
        block_id = rich_text.generate_id()
        new_blocks.append(RichTextBlock(id=block_id, type=block_type, data=block_data))

    if after_block_id is not None:
        rich_text.insert_multiple_blocks_after_id(after_block_id, new_blocks)
    else:
        # Insert at the beginning, in order
        for i, block in enumerate(new_blocks):
            rich_text.insert_block_at_index(i, block)

    doc = _get_document(documentation_id)
    _write_markdown(doc)
    ids = [b.id for b in new_blocks]
    position = f"after {after_block_id}" if after_block_id else "at the beginning"
    return f"Inserted {len(new_blocks)} block(s) {position}: {ids}"


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

    _write_markdown(_get_document(documentation_id))
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
    _write_markdown(_get_document(documentation_id))
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

    _write_markdown(_get_document(documentation_id))
    position = "beginning" if after_block_id is None else f"after {after_block_id}"
    return f"Moved block {block_id} to {position}"


# ==================== Batch & section tools ====================


def _build_blocks(rich_text: RichText, block_defs: list[dict]) -> list[RichTextBlock]:
    """Build RichTextBlock list from {type, data} dicts."""
    new_blocks: list[RichTextBlock] = []
    for block_def in block_defs:
        block_type = block_def.get("type")
        block_data = block_def.get("data")
        if not block_type or block_data is None:
            raise ValueError("Each block must have 'type' and 'data' keys.")
        block_id = rich_text.generate_id()
        new_blocks.append(RichTextBlock(id=block_id, type=block_type, data=block_data))
    return new_blocks


def _apply_update(rich_text: RichText, index: int, op: dict) -> str:
    block_id = op.get("block_id")
    data = op.get("data")
    if not block_id or data is None:
        raise ValueError(f"Operation {index}: 'update' requires 'block_id' and 'data'.")
    block = rich_text.get_block_by_id(block_id)
    if block is None:
        raise ValueError(f"Operation {index}: block '{block_id}' not found.")
    rich_text.replace_block_by_id(block_id, RichTextBlock(id=block.id, type=block.type, data=data))
    return f"updated {block_id}"


def _apply_insert(rich_text: RichText, index: int, op: dict) -> str:
    after_id = op.get("after_block_id")
    new_blocks = _build_blocks(rich_text, op.get("blocks", []))
    if after_id is not None:
        rich_text.insert_multiple_blocks_after_id(after_id, new_blocks)
    else:
        for j, block in enumerate(new_blocks):
            rich_text.insert_block_at_index(j, block)
    ids = [b.id for b in new_blocks]
    return f"inserted {len(new_blocks)} block(s): {ids}"


def _apply_remove(rich_text: RichText, index: int, op: dict) -> str:
    block_id = op.get("block_id")
    if not block_id:
        raise ValueError(f"Operation {index}: 'remove' requires 'block_id'.")
    block = rich_text.get_block_by_id(block_id)
    if block is None:
        raise ValueError(f"Operation {index}: block '{block_id}' not found.")
    rich_text.remove_block_by_id(block_id)
    return f"removed {block_id}"


_BATCH_HANDLERS = {
    "update": _apply_update,
    "insert": _apply_insert,
    "remove": _apply_remove,
}


@mcp.tool(
    name="batch_operations",
    title="Batch Operations",
    description=(
        "Execute multiple block operations in a single call.\n\n"
        "Each operation is a dict with an 'op' key and operation-specific fields:\n\n"
        '  - {"op": "update", "block_id": "...", "data": {...}}\n'
        "    Update an existing block's data (preserves id and type).\n\n"
        '  - {"op": "insert", "after_block_id": "..." or null, "blocks": [{type, data}, ...]}\n'
        "    Insert new blocks after the given block ID (or at the beginning if null).\n\n"
        '  - {"op": "remove", "block_id": "..."}\n'
        "    Remove a block by ID.\n\n"
        "Operations are applied in order. Use this instead of multiple individual "
        "tool calls when you need to make several changes at once.\n\n"
        "Args:\n"
        "  documentation_id: ID of the loaded document.\n"
        "  operations: List of operation dicts."
    ),
)
def batch_operations(documentation_id: str, operations: list[dict]) -> str:
    """Execute multiple block operations in one call."""
    rich_text = _get_document(documentation_id).rich_text
    results: list[str] = []

    for i, op in enumerate(operations):
        op_type = op.get("op")
        handler = _BATCH_HANDLERS.get(op_type)
        if handler is None:
            raise ValueError(
                f"Operation {i}: unknown op '{op_type}'. Must be 'update', 'insert', or 'remove'."
            )
        results.append(handler(rich_text, i, op))

    _write_markdown(_get_document(documentation_id))
    return f"Executed {len(operations)} operation(s): " + "; ".join(results)


@mcp.tool(
    name="replace_section",
    title="Replace Section",
    description=(
        "Replace an entire section of the document.\n\n"
        "A section starts at the given header block and includes all blocks up to "
        "(but not including) the next header of equal or higher level, or the end "
        "of the document.\n\n"
        "The header block itself is also replaced. Provide the new header as the "
        "first block in the replacement list.\n\n"
        "Args:\n"
        "  documentation_id: ID of the loaded document.\n"
        "  header_block_id: ID of the header block that starts the section.\n"
        "  new_blocks: List of {type, data} dicts that replace the entire section "
        "(including the header). The first block should typically be a header."
    ),
)
def replace_section(documentation_id: str, header_block_id: str, new_blocks: list[dict]) -> str:
    """Replace all blocks in a section (from header to next same-level header)."""
    rich_text = _get_document(documentation_id).rich_text

    header_block = rich_text.get_block_by_id(header_block_id)
    if header_block is None:
        raise ValueError(f"Block '{header_block_id}' not found.")
    if header_block.type != "header":
        raise ValueError(
            f"Block '{header_block_id}' is type '{header_block.type}', expected 'header'."
        )

    header_level = header_block.data.get("level", 2)
    header_index = rich_text.get_block_index_by_id(header_block_id)
    all_blocks = rich_text.get_blocks()

    # Find the end of the section: next header with equal or higher (lower number) level
    end_index = len(all_blocks)
    for idx in range(header_index + 1, len(all_blocks)):
        block = all_blocks[idx]
        if block.type == "header":
            block_level = block.data.get("level", 2)
            if block_level <= header_level:
                end_index = idx
                break

    # Remove old section blocks in reverse order
    removed_ids = []
    for idx in range(end_index - 1, header_index - 1, -1):
        removed_block = rich_text.remove_block_at_index(idx)
        removed_ids.append(removed_block.id)

    # Build and insert new blocks at the position where the section was
    replacement_blocks = _build_blocks(rich_text, new_blocks)
    for i, block in enumerate(replacement_blocks):
        rich_text.insert_block_at_index(header_index + i, block)

    _write_markdown(_get_document(documentation_id))
    new_ids = [b.id for b in replacement_blocks]
    return (
        f"Replaced section (removed {len(removed_ids)} block(s), "
        f"inserted {len(replacement_blocks)} block(s)): {new_ids}"
    )


mcp.run(transport="stdio")
