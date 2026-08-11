import json
import os
import zipfile
from io import BytesIO
from unittest import TestCase, mock

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.exception.exceptions.not_found_exception import NotFoundException
from gws_core.core.utils.settings import Settings
from gws_core.lab.api_registry import ApiRegistry
from gws_core.mcp.mcp_registry import META_BRICK_VERSION_KEY, McpRegistry
from gws_core.mcp.plugin_controller import get_marketplace, get_plugin_archive
from gws_core.mcp.plugin_generator import (
    MCP_SERVER_KEY,
    PLUGIN_MANIFEST_FILE_NAME,
    PLUGIN_MANIFEST_FOLDER,
    PLUGINS_ROUTE_PATH,
    PluginGenerator,
    build_archive_file_name,
)
from gws_core.mcp.plugin_identity import (
    SETTINGS_SERVED_PLUGIN_NAMES_KEY,
    build_marketplace_name,
    build_plugin_name,
    resolve_and_record_identity,
)
from gws_core.mcp.plugin_skills import inject_lab_name
from mcp.types import Icon, ToolAnnotations

# A brick name no installed brick can collide with, so a test never removes real tools.
FAKE_BRICK = "gws_fake_plugin_brick"

LAB_ID = "3f7a9c2e-4b1d-4c9a-9d2e-000000000000"


def a_tool(subject: str) -> str:
    """A tool body: only its declaration reaches the generated plugin."""
    return subject


def another_tool(subject: str, count: int = 1) -> str:
    """The same tool with one more argument, to move its schema."""
    return subject * count


class _PluginTestCase(TestCase):
    """Generates against the real registry and the real gws_core brick folder.

    Two pieces of shared state are protected: the generation cache (cleared around every
    test, since the identity a test forces must not leak into the next one) and the
    served-name history in ``Settings``, which is a real, saved file outside tests.
    """

    def setUp(self):
        PluginGenerator.clear_cache()
        self.addCleanup(PluginGenerator.clear_cache)
        self.addCleanup(McpRegistry.unregister_brick, FAKE_BRICK)

        settings = Settings.get_instance()
        self.addCleanup(
            self._restore_served_names, settings.data.get(SETTINGS_SERVED_PLUGIN_NAMES_KEY)
        )
        settings.data.pop(SETTINGS_SERVED_PLUGIN_NAMES_KEY, None)

        # The history is persisted through Settings.save, which writes the lab's real
        # settings file. Tests exercise the recording, not the file.
        saver = mock.patch.object(Settings, "save", return_value=True)
        saver.start()
        self.addCleanup(saver.stop)

    def _restore_served_names(self, previous: object) -> None:
        settings = Settings.get_instance()
        if previous is None:
            settings.data.pop(SETTINGS_SERVED_PLUGIN_NAMES_KEY, None)
        else:
            settings.data[SETTINGS_SERVED_PLUGIN_NAMES_KEY] = previous

    def lab(self, name: str = "Mon Lab", lab_id: str = LAB_ID):
        """Run inside a lab with the given name and id."""
        return mock.patch.dict(os.environ, {"LAB_NAME": name, "LAB_ID": lab_id})

    def generate(self, name: str = "Mon Lab", lab_id: str = LAB_ID):
        with self.lab(name, lab_id):
            return PluginGenerator.generate()

    def archive_files(self, archive: bytes) -> dict[str, bytes]:
        with zipfile.ZipFile(BytesIO(archive)) as zip_file:
            return {info.filename: zip_file.read(info.filename) for info in zip_file.infolist()}

    def plugin_manifest(self, archive: bytes) -> dict:
        files = self.archive_files(archive)
        return json.loads(files[f"{PLUGIN_MANIFEST_FOLDER}/{PLUGIN_MANIFEST_FILE_NAME}"])


# test_mcp_plugin
class TestIdentity(_PluginTestCase):
    """One name that may never change, one that migrates itself when it does."""

    def test_the_marketplace_name_comes_from_the_lab_id(self):
        """It has no migration path -- every user would have to add it again -- so it is
        derived from the one thing about a lab that never moves."""
        with self.lab(name="Mon Lab"):
            first = build_marketplace_name()
        with self.lab(name="Renamed Lab"):
            second = build_marketplace_name()

        self.assertEqual(first, second)
        self.assertTrue(first.startswith("constellab-"))
        self.assertIn("3f7a9c2e", first)

    def test_the_plugin_name_comes_from_the_lab_name(self):
        self.assertEqual(build_plugin_name("Mon Lab"), "mon-lab")

    def test_the_plugin_name_is_lower_cased_and_has_no_space(self):
        """Claude Code refuses a name with a space; the lowering is ours, so that
        renaming a lab from 'Mon Lab' to 'mon lab' does not read as a rename."""
        self.assertEqual(build_plugin_name("MON LAB"), build_plugin_name("mon lab"))
        self.assertNotIn(" ", build_plugin_name("Élan Vital !"))

    def test_a_lab_carrying_the_default_name_is_suffixed_from_its_id(self):
        """Two never-named labs would otherwise both produce the plugin 'lab', and
        therefore identical tool permission ids on one machine."""
        with self.lab(name="Lab"):
            name = build_plugin_name(Settings.get_lab_name())

        self.assertNotEqual(name, "lab")
        self.assertTrue(name.startswith("lab-"))
        self.assertIn("3f7a9c2e", name)

    def test_a_lab_with_an_unusable_name_is_suffixed_too(self):
        with self.lab():
            self.assertTrue(build_plugin_name("   ").startswith("lab-"))
            self.assertTrue(build_plugin_name("!!!").startswith("lab-"))

    def test_two_never_named_labs_do_not_produce_the_same_plugin_name(self):
        with self.lab(name="Lab", lab_id="aaaaaaaa-0000"):
            first = build_plugin_name("Lab")
        with self.lab(name="Lab", lab_id="bbbbbbbb-0000"):
            second = build_plugin_name("Lab")

        self.assertNotEqual(first, second)


# test_mcp_plugin
class TestServedNameHistory(_PluginTestCase):
    """A renamed plugin migrates its users through the manifest's ``renames``."""

    def test_the_served_name_is_recorded(self):
        with self.lab(name="Mon Lab"):
            resolve_and_record_identity()

        self.assertEqual(
            Settings.get_instance().data[SETTINGS_SERVED_PLUGIN_NAMES_KEY], ["mon-lab"]
        )

    def test_serving_the_same_name_twice_records_it_once(self):
        with self.lab(name="Mon Lab"):
            resolve_and_record_identity()
            identity = resolve_and_record_identity()

        self.assertEqual(
            Settings.get_instance().data[SETTINGS_SERVED_PLUGIN_NAMES_KEY], ["mon-lab"]
        )
        self.assertEqual(identity.previous_plugin_names, [])

    def test_a_rename_is_emitted_as_a_rename(self):
        with self.lab(name="Mon Lab"):
            resolve_and_record_identity()
        with self.lab(name="Notre Lab"):
            identity = resolve_and_record_identity()

        self.assertEqual(identity.plugin_name, "notre-lab")
        self.assertEqual(identity.build_renames(), {"mon-lab": "notre-lab"})

    def test_two_successive_renames_both_migrate(self):
        """A user away for both renames must still be migrated in one step, so the whole
        history is emitted, not only the last name."""
        for name in ["Mon Lab", "Notre Lab", "Leur Lab"]:
            with self.lab(name=name):
                identity = resolve_and_record_identity()

        self.assertEqual(
            identity.build_renames(), {"mon-lab": "leur-lab", "notre-lab": "leur-lab"}
        )

    def test_a_lab_renamed_back_does_not_rename_itself_away(self):
        for name in ["Mon Lab", "Notre Lab", "Mon Lab"]:
            with self.lab(name=name):
                identity = resolve_and_record_identity()

        self.assertEqual(identity.plugin_name, "mon-lab")
        self.assertEqual(identity.build_renames(), {"notre-lab": "mon-lab"})

    def test_a_settings_that_cannot_be_saved_does_not_break_the_manifest(self):
        """The degraded state is a rename that will not migrate later -- not a lab that
        stops serving its plugin."""
        with (
            mock.patch.object(Settings, "save", side_effect=OSError("read-only")),
            self.lab(name="Mon Lab"),
        ):
            identity = resolve_and_record_identity()

        self.assertEqual(identity.plugin_name, "mon-lab")


# test_mcp_plugin
class TestVersion(_PluginTestCase):
    """The version is a fingerprint of what the lab serves."""

    def test_the_version_carries_the_gws_core_version(self):
        version = self.generate().version

        self.assertTrue(version.startswith(f"{BrickHelper.get_gws_core_version()}+"))

    def test_two_generations_of_the_same_content_share_a_version(self):
        self.assertEqual(self.generate().version, self.generate().version)

    def test_a_new_tool_changes_the_version(self):
        before = self.generate().version

        McpRegistry._register(a_tool, brick_name=FAKE_BRICK, name="do_something")

        self.assertNotEqual(self.generate().version, before)

    def test_a_changed_tool_description_changes_the_version(self):
        McpRegistry._register(a_tool, brick_name=FAKE_BRICK, name="do_something", description="a")
        before = self.generate().version

        McpRegistry.unregister_brick(FAKE_BRICK)
        McpRegistry._register(a_tool, brick_name=FAKE_BRICK, name="do_something", description="b")

        self.assertNotEqual(self.generate().version, before)

    def test_a_changed_tool_signature_changes_the_version(self):
        McpRegistry._register(a_tool, brick_name=FAKE_BRICK, name="do_something")
        before = self.generate().version

        McpRegistry.unregister_brick(FAKE_BRICK)
        McpRegistry._register(another_tool, brick_name=FAKE_BRICK, name="do_something")

        self.assertNotEqual(self.generate().version, before)

    def test_every_declared_option_the_client_sees_changes_the_version(self):
        """The print covers the whole declaration, not the fields it was easy to hash:
        an option changed with nothing else would otherwise reach no installed client."""
        options = [
            {"annotations": ToolAnnotations(readOnlyHint=True)},
            {"icons": [Icon(src="https://example.com/icon.png")]},
            {"structured_output": True},
            {"title": "Do something"},
        ]
        versions = set()

        for option in [{}, *options]:
            McpRegistry.unregister_brick(FAKE_BRICK)
            McpRegistry._register(a_tool, brick_name=FAKE_BRICK, name="do_something", **option)
            versions.add(self.generate().version)

        self.assertEqual(len(versions), len(options) + 1)

    def test_a_rename_of_the_lab_changes_the_version(self):
        """Otherwise clients would keep a plugin whose name the manifest no longer
        lists, with no update to pull."""
        self.assertNotEqual(
            self.generate(name="Mon Lab").version, self.generate(name="Notre Lab").version
        )

    def test_the_version_does_not_move_with_a_brick_version(self):
        """A brick release that touched no tool must not churn every lab's plugin, so the
        tool metadata -- which carries the brick version -- is left out of the print."""
        declaration = McpRegistry._register(a_tool, brick_name=FAKE_BRICK, name="do_something")
        before = self.generate().version

        declaration.meta[META_BRICK_VERSION_KEY] = "9.9.9"

        self.assertEqual(self.generate().version, before)


# test_mcp_plugin
class TestMarketplaceManifest(_PluginTestCase):
    """What the user's single, never-changing URL answers."""

    def test_it_declares_this_lab_as_its_only_plugin(self):
        generated = self.generate()
        manifest = generated.marketplace_manifest

        self.assertEqual(manifest["name"], generated.identity.marketplace_name)
        self.assertEqual(len(manifest["plugins"]), 1)
        self.assertEqual(manifest["plugins"][0]["name"], "mon-lab")

    def test_the_archive_url_is_this_lab_and_carries_the_version(self):
        """The user is never asked for a URL, and the versioned one is what stops a proxy
        from answering a new version with a cached zip."""
        generated = self.generate()
        url = generated.marketplace_manifest["plugins"][0]["source"]["url"]

        self.assertTrue(url.startswith(Settings.get_lab_api_url().rstrip("/")))
        self.assertIn(f"/{PLUGINS_ROUTE_PATH}/", url)
        self.assertTrue(url.endswith(generated.archive_file_name))
        self.assertIn(generated.version, url)

    def test_the_source_is_an_archive(self):
        source = self.generate().marketplace_manifest["plugins"][0]["source"]

        self.assertEqual(source["source"], "archive")

    def test_the_version_is_declared_in_the_entry(self):
        """So Claude Code can see an update exists without downloading the archive."""
        generated = self.generate()

        self.assertEqual(generated.marketplace_manifest["plugins"][0]["version"], generated.version)

    def test_it_does_not_disclose_the_installed_bricks(self):
        """The manifest is public: the fingerprint carries the signal instead."""
        McpRegistry._register(a_tool, brick_name=FAKE_BRICK, name="do_something")
        manifest = json.dumps(self.generate().marketplace_manifest)

        self.assertNotIn(FAKE_BRICK, manifest)
        self.assertNotIn("gws_core", manifest)

    def test_renames_appear_only_once_the_lab_has_been_renamed(self):
        self.assertNotIn("renames", self.generate(name="Mon Lab").marketplace_manifest)

        manifest = self.generate(name="Notre Lab").marketplace_manifest

        self.assertEqual(manifest["renames"], {"mon-lab": "notre-lab"})


# test_mcp_plugin
class TestArchive(_PluginTestCase):
    """The zip the manifest points at."""

    def test_the_plugin_manifest_sits_at_the_top_of_the_archive(self):
        """Claude Code looks for .claude-plugin/ at the top or one folder deep, no
        deeper."""
        files = self.archive_files(self.generate().archive)

        self.assertIn(f"{PLUGIN_MANIFEST_FOLDER}/{PLUGIN_MANIFEST_FILE_NAME}", files)

    def test_the_plugin_points_at_this_lab_mcp_server(self):
        manifest = self.plugin_manifest(self.generate().archive)
        server = manifest["mcpServers"][MCP_SERVER_KEY]

        self.assertEqual(server["type"], "http")
        self.assertEqual(server["url"], f"{Settings.get_lab_api_url().rstrip('/')}/mcp")

    def test_the_archive_and_the_manifest_declare_the_same_version(self):
        generated = self.generate()

        self.assertEqual(self.plugin_manifest(generated.archive)["version"], generated.version)
        self.assertEqual(
            build_archive_file_name(generated.identity.plugin_name, generated.version),
            generated.archive_file_name,
        )

    def test_the_archive_is_deterministic(self):
        """Same content, same bytes -- which is what makes the version identity honest."""
        self.assertEqual(self.generate().archive, self.generate().archive)

    def test_the_gws_core_skill_is_shipped(self):
        generated = self.generate()

        self.assertIn("skills/gws_core/query-lab-db/SKILL.md", self.archive_files(generated.archive))
        self.assertIn(
            "./skills/gws_core/query-lab-db", self.plugin_manifest(generated.archive)["skills"]
        )

    def test_the_lab_name_is_injected_into_the_shipped_skill(self):
        """Two labs installed side by side otherwise expose identically-described
        skills, and the description is what the model reads when choosing."""
        files = self.archive_files(self.generate(name="Mon Lab").archive)
        skill = files["skills/gws_core/query-lab-db/SKILL.md"].decode("utf-8")

        self.assertIn("Mon Lab", skill)

    def test_the_shipped_skill_names_the_tools_it_drives(self):
        files = self.archive_files(self.generate().archive)
        skill = files["skills/gws_core/query-lab-db/SKILL.md"].decode("utf-8")

        self.assertIn("gws_core_db_list", skill)
        self.assertIn("gws_core_db_query", skill)


# test_mcp_plugin
class TestSkillLabNameInjection(TestCase):
    """Rewriting a skill's description, without a YAML dependency to do it."""

    def _description(self, content: str) -> str:
        for line in content.splitlines():
            if line.startswith("description:"):
                return line
        return ""

    def test_the_lab_name_goes_first(self):
        content = inject_lab_name("---\nname: s\ndescription: Do a thing.\n---\nBody\n", "Mon Lab", "s")

        self.assertIn("Mon Lab", self._description(content))
        self.assertIn("Do a thing.", self._description(content))
        self.assertIn("Body", content)

    def test_a_quoted_description_is_rewritten_once(self):
        for raw in ['"Do a thing."', "'Do a thing.'"]:
            content = inject_lab_name(f"---\ndescription: {raw}\n---\nBody\n", "Mon Lab", "s")

            self.assertIn("Do a thing.", self._description(content))
            self.assertEqual(content.count("description:"), 1)

    def test_a_lab_name_with_a_quote_does_not_break_the_front_matter(self):
        content = inject_lab_name(
            "---\ndescription: Do a thing.\n---\nBody\n", 'L"ab: the "one"', "s"
        )
        description = self._description(content)

        self.assertTrue(description.startswith('description: "'))
        self.assertTrue(description.endswith('"'))

    def test_the_rest_of_the_front_matter_is_untouched(self):
        content = inject_lab_name(
            "---\nname: s\ndescription: Do a thing.\nallowed-tools: Read\n---\nBody\n",
            "Mon Lab",
            "s",
        )

        self.assertIn("name: s", content)
        self.assertIn("allowed-tools: Read", content)

    def test_a_skill_with_no_front_matter_is_left_alone(self):
        content = "# Just a title\n"

        self.assertEqual(inject_lab_name(content, "Mon Lab", "s"), content)

    def test_a_description_that_cannot_be_read_is_left_alone(self):
        """A skill shipped undescribed beats one shipped with broken front matter."""
        content = "---\nname: s\ndescription: |\n  A long one.\n---\nBody\n"

        self.assertEqual(inject_lab_name(content, "Mon Lab", "s"), content)


# test_mcp_plugin
class TestRoutes(_PluginTestCase):
    """What the two public routes answer."""

    def test_the_marketplace_route_serves_the_manifest(self):
        response = get_marketplace()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.body), PluginGenerator.get_generated().marketplace_manifest
        )

    def test_the_archive_route_serves_the_zip_under_its_versioned_name(self):
        generated = PluginGenerator.get_generated()

        response = get_plugin_archive(generated.archive_file_name)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, generated.archive)
        self.assertEqual(response.media_type, "application/zip")

    def test_another_version_is_a_404_saying_what_to_do(self):
        """A client holding a manifest from before an upgrade must not be handed the
        current archive under a URL announcing another version."""
        generated = PluginGenerator.get_generated()

        with self.assertRaises(NotFoundException) as raised:
            get_plugin_archive("mon-lab-0.0.1+deadbeef.zip")

        detail = raised.exception.detail

        self.assertEqual(raised.exception.status_code, 404)
        self.assertIn(generated.version, detail)
        self.assertIn("marketplace update", detail)
        self.assertIn(generated.identity.marketplace_name, detail)

    def test_the_routes_are_not_registered_when_mcp_is_disabled(self):
        """They are registered from the same block that mounts /mcp/, so importing
        gws_core must not create them on its own."""
        self.assertNotIn(f"/{PLUGINS_ROUTE_PATH}/", ApiRegistry.get_all_apis())
