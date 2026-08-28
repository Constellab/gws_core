"""Registry of the MCP tools declared by the lab's bricks.

The lab mounts **one** MCP server (see :mod:`gws_core.mcp.mcp_controller`) and every
brick contributes its tools to it. A brick never stands up a server of its own: two
servers would mean two dynamic client registrations, two browser consent round-trips
and two refreshing tokens, for bricks that already share the lab's ``secret_key`` and
``User``.

Registration is a decorator filled at brick import and consumed when the server is
built, on the model of :class:`~gws_core.lab.api_registry.ApiRegistry`. It works
because ``BrickService.import_all_bricks_in_python`` imports every module of every
brick well before ``mount_mcp_app`` runs, so the registry is complete by then.

The options mirror ``FastMCP.add_tool`` (``name``, ``title``, ``description``,
``annotations``, ``icons``, ``meta``, ``structured_output``) rather than inventing a
parallel vocabulary: whatever the SDK can express about a tool is expressible here.

Two rules the registry enforces, both at declaration time:

- **Every tool name is prefixed with its brick name.** Tool names end up in users'
  permission rules, so a collision discovered in production would be paid for with a
  rename that breaks those rules silently. A name that already carries its own prefix
  is an error, not a silent double prefix.
- **A name is served once.** Prefixing makes same-name-different-brick collisions
  impossible, but ``gws_a`` declaring ``b_foo`` and ``gws_a_b`` declaring ``foo`` still
  meet at ``gws_a_b_foo``. That fails, naming both bricks.

Because the served tool set is a function of which bricks are installed, the server
can no longer promise anything about the tools as a whole -- in particular not that
they are read-only. That property now belongs to each tool, carried by its
``readOnlyHint`` annotation and its own description.

**Authorization is each brick's job.** The token an MCP client holds is a full,
unscoped lab session: authentication is not authorization. A tool that exposes
anything sensitive checks the calling user's rights itself.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import Icon, ToolAnnotations

from gws_core.brick.brick_helper import BrickHelper

# Reserved ``meta`` keys, set by the registry on every declared tool. Keys supplied by
# the tool's author are preserved alongside them.
META_BRICK_KEY = "brick"
META_BRICK_VERSION_KEY = "brick_version"


class McpToolDeclarationError(Exception):
    """Raised when a brick declares a tool the registry refuses to serve.

    Raised while the brick is being imported, so the brick's load stops and
    ``BrickService`` logs it as ``CRITICAL`` against that brick -- the tool never
    reaches the served set.
    """


@dataclass(frozen=True)
class McpToolDeclaration:
    """One tool a brick declared, holding everything ``FastMCP.add_tool`` needs.

    :param function: The Python function implementing the tool.
    :param name: The served name, brick prefix included.
    :param declared_name: The name as the brick wrote it, without the prefix. Kept for
        error messages, which are read by the brick's author.
    :param brick_name: Name of the declaring brick.
    :param brick_version: Version of the declaring brick, ``None`` when unknown.

    The remaining fields are ``FastMCP.add_tool``'s own options, carried verbatim from the
    declaration to :meth:`add_to_server`. Only ``meta`` is not verbatim: the registry adds
    its reserved keys to it (see :data:`META_BRICK_KEY`).
    """

    function: Callable[..., Any]
    name: str
    declared_name: str
    brick_name: str
    brick_version: str | None
    title: str | None
    description: str | None
    annotations: ToolAnnotations | None
    icons: list[Icon] | None
    meta: dict[str, Any]
    structured_output: bool | None

    def add_to_server(self, server: FastMCP) -> None:
        """Add this tool to an MCP server under its prefixed name."""
        server.add_tool(
            self.function,
            name=self.name,
            title=self.title,
            description=self.description,
            annotations=self.annotations,
            icons=self.icons,
            meta=self.meta,
            structured_output=self.structured_output,
        )


@dataclass(frozen=True)
class McpBrickContribution:
    """The tools one brick contributes to the lab's MCP server.

    :param brick_name: The contributing brick.
    :param brick_version: Its version, ``None`` when unknown.
    :param tools: Its declared tools, ordered by served name.
    """

    brick_name: str
    brick_version: str | None
    tools: list[McpToolDeclaration]


class McpRegistry:
    """Registry of the MCP tools the lab's bricks declare.

    Usage from a brick::

        from gws_core import McpRegistry
        from mcp.types import ToolAnnotations

        @McpRegistry.register_tool(
            "list_campaigns",
            title="List investment campaigns",
            description="List the lab's investment campaigns, most recent first.",
            annotations=ToolAnnotations(readOnlyHint=True),
        )
        def list_campaigns() -> list[dict]:
            # The MCP token is an unscoped lab session: check the caller's rights here.
            ...

    The tool above is served as ``gws_invest_list_campaigns``. The docstring and type
    hints of the function become the tool's schema, exactly as with the MCP SDK.
    """

    # served (prefixed) tool name -> declaration
    _tools: dict[str, McpToolDeclaration] = {}

    @classmethod
    def register_tool(
        cls,
        name: str | None = None,
        title: str | None = None,
        description: str | None = None,
        annotations: ToolAnnotations | None = None,
        icons: list[Icon] | None = None,
        meta: dict[str, Any] | None = None,
        structured_output: bool | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorate a function to serve it as an MCP tool of the declaring brick.

        The declaring brick is read from the function's module, and the served name is
        prefixed with it. Every parameter is passed through to ``FastMCP.add_tool``.

        The decorated function is returned unchanged, so it stays directly callable
        (and directly testable) outside MCP.

        :param name: Tool name **without** the brick prefix, which the registry adds.
            Defaults to the function's name. A name that already starts with the brick
            prefix raises :class:`McpToolDeclarationError`.
        :param title: Human-readable title shown by clients.
        :param description: What the tool does, read by the calling model. Keep it
            tight: every description sits in every session connected to the lab.
        :param annotations: The SDK's tool hints (``readOnlyHint``, ``destructiveHint``,
            ``idempotentHint``, ``openWorldHint``). Declare ``readOnlyHint=True`` on a
            tool that only reads -- the server makes no such promise on its behalf.
        :param icons: Icons for clients that display them.
        :param meta: Free-form metadata. Merged with the registry's own ``brick`` and
            ``brick_version`` keys, which take precedence.
        :param structured_output: Passed through to the SDK (``None`` lets it decide
            from the return type).
        :raises McpToolDeclarationError: If the name is already prefixed, or another
            brick already serves it.
        """

        def decorator(function: Callable[..., Any]) -> Callable[..., Any]:
            cls._register(
                function,
                brick_name=BrickHelper.get_brick_name(function),
                name=name,
                title=title,
                description=description,
                annotations=annotations,
                icons=icons,
                meta=meta,
                structured_output=structured_output,
            )
            return function

        return decorator

    @classmethod
    def _register(
        cls,
        function: Callable[..., Any],
        brick_name: str,
        name: str | None = None,
        title: str | None = None,
        description: str | None = None,
        annotations: ToolAnnotations | None = None,
        icons: list[Icon] | None = None,
        meta: dict[str, Any] | None = None,
        structured_output: bool | None = None,
    ) -> McpToolDeclaration:
        """Store one declaration, for a brick named explicitly.

        Private on purpose. The decorator is the only way in, because it reads the brick
        from the function's own module: a brick able to name *another* brick here could
        serve a tool under that brick's prefix and ``meta.brick``, and would survive that
        brick being dropped. Tests reach this directly, which is what lets them use brick
        names no installed brick has.

        :param function: The function implementing the tool.
        :param brick_name: The declaring brick.
        :return: The stored declaration.
        :raises McpToolDeclarationError: See :meth:`register_tool`.
        """
        declared_name = name or function.__name__
        tool_name = cls.build_tool_name(brick_name, declared_name)

        cls._check_name_is_not_prefixed(brick_name, declared_name)
        cls._check_name_is_free(brick_name, declared_name, tool_name)

        brick_info = BrickHelper.get_brick_info(brick_name)
        brick_version = brick_info.version if brick_info else None

        declaration = McpToolDeclaration(
            function=function,
            name=tool_name,
            declared_name=declared_name,
            brick_name=brick_name,
            brick_version=brick_version,
            title=title,
            description=description,
            annotations=annotations,
            icons=icons,
            # The reserved keys are applied last: where a tool came from is not the
            # author's to override.
            meta={
                **(meta or {}),
                META_BRICK_KEY: brick_name,
                META_BRICK_VERSION_KEY: brick_version,
            },
            structured_output=structured_output,
        )

        cls._tools[tool_name] = declaration
        return declaration

    @classmethod
    def build_tool_name(cls, brick_name: str, declared_name: str) -> str:
        """Return the served name of a tool: its declared name, brick-prefixed.

        The one place the prefix is applied, so a brick that has to name one of its own
        tools in prose (a description pointing at a companion tool) can ask for it
        instead of hard-coding the rule.
        """
        return f"{brick_name}_{declared_name}"

    @classmethod
    def _check_name_is_not_prefixed(cls, brick_name: str, declared_name: str) -> None:
        """Refuse a name that already carries its own brick prefix.

        Prefixing it again would serve ``gws_invest_gws_invest_foo``, which nobody
        meant and which the author would only discover from a client's tool list.

        What is refused is the prefix as the registry writes it -- ``<brick>_``, or the
        brick name alone. A name that merely *starts like* its brick's name is fine:
        ``gws_invest`` may declare ``investor_count``, and would be told to rename a tool
        that only shares a few letters with its brick for no reason.
        """
        if declared_name != brick_name and not declared_name.startswith(f"{brick_name}_"):
            return

        message = (
            f"Brick '{brick_name}' declares the MCP tool '{declared_name}', which already "
            "carries its own brick prefix. The registry adds that prefix itself"
        )
        without_prefix = declared_name[len(brick_name) :].lstrip("_")

        if not without_prefix:
            raise McpToolDeclarationError(f"{message}, so name the tool after what it does.")

        raise McpToolDeclarationError(
            f"{message}: declare the tool as '{without_prefix}' to have it served as "
            f"'{cls.build_tool_name(brick_name, without_prefix)}'."
        )

    @classmethod
    def _check_name_is_free(cls, brick_name: str, declared_name: str, tool_name: str) -> None:
        """Refuse a served name another declaration already holds.

        Two bricks reach the same served name when one brick's name is a prefix of the
        other's (``gws_a`` declaring ``b_foo``, ``gws_a_b`` declaring ``foo``). Both are
        named in the message, since neither author can see the other's declaration.
        """
        existing = cls._tools.get(tool_name)
        if existing is None:
            return

        raise McpToolDeclarationError(
            f"The MCP tool name '{tool_name}' is already served: brick "
            f"'{existing.brick_name}' declares it as '{existing.declared_name}', and brick "
            f"'{brick_name}' declares it as '{declared_name}'. One of them must be renamed."
        )

    @classmethod
    def get_tools(cls) -> list[McpToolDeclaration]:
        """Every declared tool, ordered by served name.

        Ordered so the served tool list -- and anything derived from it, such as a
        fingerprint of the tools -- does not depend on brick import order.
        """
        return [cls._tools[name] for name in sorted(cls._tools)]

    @classmethod
    def get_contributions(cls) -> list[McpBrickContribution]:
        """The declared tools grouped by brick, both levels ordered by name."""
        by_brick: dict[str, list[McpToolDeclaration]] = {}
        for tool in cls.get_tools():
            by_brick.setdefault(tool.brick_name, []).append(tool)

        return [
            McpBrickContribution(
                brick_name=brick_name,
                brick_version=tools[0].brick_version,
                tools=tools,
            )
            for brick_name, tools in sorted(by_brick.items())
        ]

    @classmethod
    def unregister_brick(cls, brick_name: str) -> list[str]:
        """Drop every tool of a brick that must not be served.

        Called when a brick's import failed part-way: its modules are imported in
        order, so tools declared before the failing one are already registered while
        the brick as a whole never finished loading. Serving that half is the worst of
        the three possible states -- the client sees a tool set no version of the brick
        ever had. Same precedent as
        ``TypingManager.unregister_unresolvable_typings``.

        Reporting is left to the caller, which returns the dropped names rather than
        logging them: the caller knows *why* the brick is being dropped, and can log it
        against the brick itself through ``BrickLogService``.

        :param brick_name: The brick whose tools are dropped.
        :return: The served names that were dropped, ordered as :meth:`get_tools`.
        """
        dropped = sorted(name for name, tool in cls._tools.items() if tool.brick_name == brick_name)

        for name in dropped:
            del cls._tools[name]

        return dropped
