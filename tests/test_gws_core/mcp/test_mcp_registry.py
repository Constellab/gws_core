import asyncio
from unittest import TestCase

from gws_core.brick.brick_helper import BrickHelper
from gws_core.mcp.db_mcp import DB_LIST_TOOL_NAME, db_list, db_query
from gws_core.mcp.mcp_registry import (
    META_BRICK_KEY,
    META_BRICK_VERSION_KEY,
    McpBrickContribution,
    McpRegistry,
    McpToolDeclaration,
    McpToolDeclarationError,
)
from gws_core.mcp.mcp_server_builder import build_instructions, build_mcp_server
from gws_core.oauth.oauth_provider import LabOAuthProvider
from gws_core.test.base_test_case import BaseTestCase
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from mcp.types import Tool, ToolAnnotations
from pydantic import AnyHttpUrl

LAB_HOST = "lab.example.com"
MCP_URL = f"https://{LAB_HOST}/mcp"

# A brick name no installed brick can collide with, so a test never removes real tools.
FAKE_BRICK = "gws_fake_brick"
OTHER_FAKE_BRICK = "gws_other_fake_brick"


def a_tool() -> str:
    """A tool body: what it returns is irrelevant, only its declaration is tested."""
    return "ok"


class _RegistryTestCase(TestCase):
    """Registers into the real registry, under brick names nothing else uses.

    The registry is class-level state filled at brick import, and the real tools of the
    installed bricks are in it for the whole test process -- there is no way to register
    them again once dropped, since their modules are already imported. So a test never
    empties the registry: it adds tools under fake brick names and removes exactly those.

    ``_register`` is reached directly (rather than the decorator) because it is the only
    way to declare under an arbitrary brick name, which is what the naming rules need.
    """

    def setUp(self):
        self.addCleanup(McpRegistry.unregister_brick, FAKE_BRICK)
        self.addCleanup(McpRegistry.unregister_brick, OTHER_FAKE_BRICK)

    def register(self, brick_name: str = FAKE_BRICK, **kwargs) -> McpToolDeclaration:
        return McpRegistry._register(a_tool, brick_name=brick_name, **kwargs)


# test_mcp_registry
class TestToolNaming(_RegistryTestCase):
    """Names end up in users' permission rules, so the registry owns them."""

    def test_the_served_name_is_prefixed_with_the_declaring_brick(self):
        declaration = self.register(name="list_campaigns")

        self.assertEqual(declaration.name, f"{FAKE_BRICK}_list_campaigns")
        self.assertEqual(declaration.declared_name, "list_campaigns")

    def test_the_name_defaults_to_the_function_name(self):
        self.assertEqual(self.register().name, f"{FAKE_BRICK}_a_tool")

    def test_the_decorator_reads_the_brick_from_the_declaring_module(self):
        """The decorator's whole added value over ``register``: the brick cannot be
        misdeclared, because it is read from where the function lives."""
        test_brick = BrickHelper.get_brick_name(a_tool)
        self.addCleanup(McpRegistry.unregister_brick, test_brick)

        @McpRegistry.register_tool("declared_by_decorator")
        def decorated() -> str:
            return "ok"

        served = McpRegistry.build_tool_name(test_brick, "declared_by_decorator")
        self.assertIn(served, [tool.name for tool in McpRegistry.get_tools()])
        # Returned unchanged, so the function stays callable and testable outside MCP.
        self.assertEqual(decorated(), "ok")

    def test_a_name_that_already_carries_its_prefix_is_refused(self):
        """Prefixing it again would serve gws_fake_brick_gws_fake_brick_foo, which the
        author would only ever discover from a client's tool list."""
        with self.assertRaises(McpToolDeclarationError) as raised:
            self.register(name=f"{FAKE_BRICK}_foo")

        message = str(raised.exception)
        self.assertIn(FAKE_BRICK, message)
        self.assertIn(f"{FAKE_BRICK}_foo", message)
        # The message states the name to declare instead.
        self.assertIn("'foo'", message)

    def test_a_name_equal_to_the_brick_name_is_refused(self):
        """Stripping the prefix would leave nothing, so the message cannot suggest a
        replacement -- it must still be readable."""
        with self.assertRaises(McpToolDeclarationError) as raised:
            self.register(name=FAKE_BRICK)

        self.assertIn(FAKE_BRICK, str(raised.exception))
        self.assertNotIn("''", str(raised.exception))

    def test_a_name_that_merely_starts_like_the_brick_name_is_allowed(self):
        """Only the prefix as the registry writes it ('<brick>_') is refused. Refusing
        every name that shares a few letters with its brick would reject 'investor_count'
        declared by 'gws_invest' for no reason."""
        declaration = self.register(name=f"{FAKE_BRICK}s_count")

        self.assertEqual(declaration.name, f"{FAKE_BRICK}_{FAKE_BRICK}s_count")

    def test_a_refused_name_is_not_registered(self):
        with self.assertRaises(McpToolDeclarationError):
            self.register(name=f"{FAKE_BRICK}_foo")

        self.assertEqual(
            [tool for tool in McpRegistry.get_tools() if tool.brick_name == FAKE_BRICK], []
        )

    def test_two_bricks_reaching_the_same_served_name_are_both_named(self):
        """Prefixing rules out same-name collisions, but one brick name being a prefix
        of another still lets two declarations meet: gws_fake_brick + 'x_foo' and
        gws_fake_brick_x + 'foo' are both gws_fake_brick_x_foo."""
        nested_brick = f"{FAKE_BRICK}_x"
        self.addCleanup(McpRegistry.unregister_brick, nested_brick)

        first = self.register(name="x_foo")

        with self.assertRaises(McpToolDeclarationError) as raised:
            self.register(brick_name=nested_brick, name="foo")

        message = str(raised.exception)
        self.assertEqual(first.name, f"{FAKE_BRICK}_x_foo")
        self.assertIn(FAKE_BRICK, message)
        self.assertIn(nested_brick, message)
        self.assertIn("x_foo", message)

    def test_the_same_brick_declaring_a_name_twice_is_refused(self):
        self.register(name="foo")

        with self.assertRaises(McpToolDeclarationError):
            self.register(name="foo")

    def test_build_tool_name_is_the_single_place_the_prefix_is_applied(self):
        self.assertEqual(McpRegistry.build_tool_name("gws_invest", "foo"), "gws_invest_foo")


# test_mcp_registry
class TestToolMetadata(_RegistryTestCase):
    """What the registry adds to a declaration, and what it leaves alone."""

    def test_meta_carries_the_declaring_brick_and_its_version(self):
        declaration = self.register()

        self.assertEqual(declaration.meta[META_BRICK_KEY], FAKE_BRICK)
        self.assertEqual(
            declaration.meta[META_BRICK_VERSION_KEY], declaration.brick_version
        )
        self.assertIsNotNone(declaration.brick_version)

    def test_meta_keys_from_the_author_are_preserved(self):
        declaration = self.register(meta={"stability": "beta"})

        self.assertEqual(declaration.meta["stability"], "beta")
        self.assertEqual(declaration.meta[META_BRICK_KEY], FAKE_BRICK)

    def test_the_reserved_keys_cannot_be_overridden(self):
        """Where a tool came from is not the author's to rewrite."""
        declaration = self.register(meta={META_BRICK_KEY: "not_this_brick"})

        self.assertEqual(declaration.meta[META_BRICK_KEY], FAKE_BRICK)

    def test_every_add_tool_option_is_carried_through(self):
        annotations = ToolAnnotations(readOnlyHint=True)

        declaration = self.register(
            name="foo",
            title="A title",
            description="A description",
            annotations=annotations,
            structured_output=True,
        )

        self.assertEqual(declaration.title, "A title")
        self.assertEqual(declaration.description, "A description")
        self.assertEqual(declaration.annotations, annotations)
        self.assertTrue(declaration.structured_output)
        self.assertIs(declaration.function, a_tool)


# test_mcp_registry
class TestRegistryReads(_RegistryTestCase):
    """How the server (and, later, the plugin generator) reads the registry."""

    def test_tools_are_ordered_by_served_name(self):
        """Ordered, so the served list does not depend on brick import order."""
        self.register(name="b_tool")
        self.register(name="a_tool")

        names = [tool.name for tool in McpRegistry.get_tools() if tool.brick_name == FAKE_BRICK]
        self.assertEqual(names, sorted(names))

    def test_contributions_group_the_tools_by_brick(self):
        self.register(name="one")
        self.register(name="two")
        self.register(brick_name=OTHER_FAKE_BRICK, name="three")

        contributions = {c.brick_name: c for c in McpRegistry.get_contributions()}

        self.assertEqual(
            [tool.declared_name for tool in contributions[FAKE_BRICK].tools], ["one", "two"]
        )
        self.assertEqual(
            [tool.declared_name for tool in contributions[OTHER_FAKE_BRICK].tools], ["three"]
        )
        self.assertEqual(
            contributions[FAKE_BRICK].brick_version,
            contributions[FAKE_BRICK].tools[0].brick_version,
        )

    def test_contributions_are_ordered_by_brick_name(self):
        self.register(brick_name=OTHER_FAKE_BRICK, name="three")
        self.register(name="one")

        names = [c.brick_name for c in McpRegistry.get_contributions()]
        self.assertEqual(names, sorted(names))


# test_mcp_registry
class TestBrickInError(_RegistryTestCase):
    """A brick that did not load completely is dropped whole."""

    def test_a_bricks_tools_are_all_dropped(self):
        """Its modules import in order, so the tools declared before the failing one are
        already registered -- a set no version of the brick ever served."""
        self.register(name="declared_before_the_failure")

        dropped = McpRegistry.unregister_brick(FAKE_BRICK)

        self.assertEqual(dropped, [f"{FAKE_BRICK}_declared_before_the_failure"])
        self.assertEqual(
            [tool for tool in McpRegistry.get_tools() if tool.brick_name == FAKE_BRICK], []
        )

    def test_the_dropped_names_are_returned_for_the_caller_to_report(self):
        """BrickService logs them as CRITICAL against the brick, so they must come back."""
        self.register(name="second")
        self.register(name="first")

        self.assertEqual(
            McpRegistry.unregister_brick(FAKE_BRICK),
            [f"{FAKE_BRICK}_first", f"{FAKE_BRICK}_second"],
        )

    def test_the_other_bricks_are_untouched(self):
        self.register(name="dropped")
        kept = self.register(brick_name=OTHER_FAKE_BRICK, name="kept")

        McpRegistry.unregister_brick(FAKE_BRICK)

        self.assertIn(kept.name, [tool.name for tool in McpRegistry.get_tools()])

    def test_dropping_a_brick_that_declared_nothing_is_a_no_op(self):
        before = [tool.name for tool in McpRegistry.get_tools()]

        self.assertEqual(McpRegistry.unregister_brick("gws_brick_that_declares_nothing"), [])
        self.assertEqual([tool.name for tool in McpRegistry.get_tools()], before)

    def test_a_brick_whose_name_prefixes_another_does_not_drop_its_tools(self):
        """Dropping 'gws_fake_brick' must not take 'gws_fake_brick_x' with it."""
        nested_brick = f"{FAKE_BRICK}_x"
        self.addCleanup(McpRegistry.unregister_brick, nested_brick)
        nested = self.register(brick_name=nested_brick, name="kept")

        McpRegistry.unregister_brick(FAKE_BRICK)

        self.assertIn(nested.name, [tool.name for tool in McpRegistry.get_tools()])

    def test_a_dropped_name_is_free_again(self):
        """The brick may be fixed and the lab restarted; nothing must linger."""
        self.register(name="foo")
        McpRegistry.unregister_brick(FAKE_BRICK)

        self.assertEqual(self.register(name="foo").name, f"{FAKE_BRICK}_foo")


# test_mcp_registry
class TestServerInstructions(TestCase):
    """The server describes itself from the bricks contributing to it."""

    def _contribution(self, brick_name: str, version: str | None, *names: str):
        return McpBrickContribution(
            brick_name=brick_name,
            brick_version=version,
            tools=[
                McpToolDeclaration(
                    function=a_tool,
                    name=McpRegistry.build_tool_name(brick_name, name),
                    declared_name=name,
                    brick_name=brick_name,
                    brick_version=version,
                    title=None,
                    description=None,
                    annotations=None,
                    icons=None,
                    meta={},
                    structured_output=None,
                )
                for name in names
            ],
        )

    def test_the_contributing_bricks_and_their_tools_are_listed(self):
        instructions = build_instructions(
            [
                self._contribution("gws_core", "1.2.3", "db_list"),
                self._contribution("gws_invest", "0.1.0", "list_campaigns"),
            ]
        )

        self.assertIn("gws_core 1.2.3", instructions)
        self.assertIn("gws_core_db_list", instructions)
        self.assertIn("gws_invest 0.1.0", instructions)
        self.assertIn("gws_invest_list_campaigns", instructions)

    def test_the_prefixing_rule_is_explained(self):
        """The one thing about the names a client cannot work out for itself."""
        instructions = build_instructions([self._contribution("gws_core", "1.2.3", "db_list")])

        self.assertIn("prefixed", instructions)

    def test_the_server_makes_no_read_only_promise(self):
        """Regression: the server used to state it was read-only, which stopped being
        true the moment any brick declared a mutating tool."""
        instructions = build_instructions([self._contribution("gws_invest", "0.1.0", "pay")])

        self.assertNotIn("read-only", instructions.lower())
        self.assertNotIn("writes are blocked", instructions.lower())

    def test_a_brick_with_an_unknown_version_is_still_listed(self):
        instructions = build_instructions([self._contribution("gws_core", None, "db_list")])

        self.assertIn("gws_core", instructions)
        self.assertNotIn("None", instructions)

    def test_a_lab_with_no_tool_says_so(self):
        self.assertIn("no MCP tool", build_instructions([]))


# test_mcp_registry
class TestServerServesTheRegistry(_RegistryTestCase):
    """The built server serves what the registry holds, and nothing else."""

    def _build_server(self):
        return build_mcp_server(
            auth_provider=LabOAuthProvider(
                consent_page_url=f"https://{LAB_HOST}/oauth-consent",
                resource_url=MCP_URL,
                resource_name="MCP server",
                lab_url=f"https://{LAB_HOST}",
            ),
            auth_settings=AuthSettings(
                issuer_url=AnyHttpUrl(MCP_URL),
                resource_server_url=AnyHttpUrl(MCP_URL),
                client_registration_options=ClientRegistrationOptions(enabled=True),
            ),
            allowed_hosts=[LAB_HOST],
        )

    def _served_tools(self) -> dict[str, Tool]:
        server = self._build_server()
        return {tool.name: tool for tool in asyncio.run(server.list_tools())}

    def test_a_declared_tool_is_served_under_its_prefixed_name(self):
        self.register(name="list_campaigns", description="List them.")

        served = self._served_tools()

        self.assertIn(f"{FAKE_BRICK}_list_campaigns", served)
        self.assertNotIn("list_campaigns", served)

    def test_the_served_tool_carries_its_annotations_and_meta(self):
        self.register(name="foo", annotations=ToolAnnotations(readOnlyHint=True))

        tool = self._served_tools()[f"{FAKE_BRICK}_foo"]

        assert tool.annotations is not None
        self.assertTrue(tool.annotations.readOnlyHint)
        assert tool.meta is not None
        self.assertEqual(tool.meta[META_BRICK_KEY], FAKE_BRICK)

    def test_the_server_instructions_come_from_the_registry(self):
        self.register(name="foo")

        self.assertIn(FAKE_BRICK, self._build_server().instructions or "")

    def test_a_dropped_brick_is_not_served(self):
        self.register(name="foo")
        McpRegistry.unregister_brick(FAKE_BRICK)

        self.assertNotIn(f"{FAKE_BRICK}_foo", self._served_tools())


# test_mcp_registry
class TestDbToolsThroughTheRegistry(TestCase):
    """gws_core's own tools go through the registry like any other brick's."""

    def _db_tools(self) -> dict[str, McpToolDeclaration]:
        return {tool.name: tool for tool in McpRegistry.get_tools()}

    def test_the_db_tools_are_declared_under_their_prefixed_names(self):
        served = self._db_tools()

        self.assertIn("gws_core_db_list", served)
        self.assertIn("gws_core_db_query", served)
        self.assertEqual(DB_LIST_TOOL_NAME, "gws_core_db_list")

    def test_the_db_tools_are_declared_by_gws_core_with_no_special_path(self):
        tool = self._db_tools()["gws_core_db_query"]

        self.assertEqual(tool.brick_name, "gws_core")
        self.assertEqual(tool.meta[META_BRICK_KEY], "gws_core")
        self.assertEqual(tool.meta[META_BRICK_VERSION_KEY], BrickHelper.get_gws_core_version())

    def test_the_db_tools_are_annotated_read_only(self):
        """The promise moved off the server: each tool carries it now."""
        for name in ["gws_core_db_list", "gws_core_db_query"]:
            annotations = self._db_tools()[name].annotations
            assert annotations is not None
            self.assertTrue(annotations.readOnlyHint)
            self.assertFalse(annotations.destructiveHint)

    def test_each_db_tool_names_its_companion_by_its_served_name(self):
        """A description pointing at 'db_list' would name a tool that does not exist."""
        tools = self._db_tools()

        self.assertIn("gws_core_db_list", tools["gws_core_db_query"].description or "")
        self.assertIn("gws_core_db_query", tools["gws_core_db_list"].description or "")


# test_mcp_registry
class TestDbToolsBehaviour(BaseTestCase):
    """The tools behave as before the move onto the registry.

    They are plain functions the decorator returned unchanged, so they are called
    directly here -- what the registry did to them is covered above.
    """

    def test_a_read_only_query_returns_its_rows(self):
        result = db_query(sql="SELECT 1 AS one, 2 AS two")

        self.assertEqual(result["columns"], ["one", "two"])
        self.assertEqual(result["rows"], [{"one": 1, "two": 2}])
        self.assertEqual(result["row_count"], 1)
        self.assertFalse(result["truncated"])

    def test_a_non_read_only_statement_is_still_rejected(self):
        """The read-only guard is the tool's promise now, so it stays tested here."""
        with self.assertRaises(ValueError):
            db_query(sql="DELETE FROM gws_user")

    def test_the_row_limit_still_truncates(self):
        result = db_query(sql="SELECT 1 AS n UNION SELECT 2 AS n", limit=1)

        self.assertEqual(result["row_count"], 1)
        self.assertTrue(result["truncated"])

    def test_db_list_returns_the_brick_databases(self):
        self.assertIn("gws_core", db_list())
