import json
import os
import threading
import zipfile
from unittest import TestCase
from unittest.mock import patch

from gws_core.apps.app_plugin_downloader import AppPluginDownloader
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper


class _TestPlugin(AppPluginDownloader):
    """Plugin with a materialize target and an environment file, like ReflexPlugin."""

    def __init__(self, target: str):
        super().__init__(
            package_name=AppPluginDownloader.REFLEX_COMPONENTS, materialize_target=target
        )

    def get_base_href(self) -> str:
        return "external/gws_plugin"

    def pre_materialize_finalize(self, staging_folder: str) -> None:
        self.create_environment_json_file(staging_folder)


def _make_fake_package_zip(dest_folder: str, version: str) -> str:
    """Build a zip with the same layout as a real plugin package."""
    zip_path = os.path.join(dest_folder, "package.zip")
    with zipfile.ZipFile(zip_path, "w") as zip_file:
        zip_file.writestr("version.json", json.dumps({"version": version}))
        zip_file.writestr("index.html", "<html></html>")
        zip_file.writestr("assets/main.js", "console.log('hi')")
    return zip_path


# test_app_plugin_downloader
class TestAppPluginDownloader(TestCase):
    """Atomic, concurrency-safe plugin install (issue #103).

    The download is faked (no network): `FileDownloader.download_file` is patched to
    produce a local zip with the expected package layout.
    """

    download_count: int

    def setUp(self) -> None:
        self.download_count = 0
        self.temp_dir = Settings.make_temp_dir()
        self.target = os.path.join(self.temp_dir, "app", "assets", "external", "gws_plugin")
        # isolate the store between tests
        downloader = AppPluginDownloader(AppPluginDownloader.REFLEX_COMPONENTS)
        FileHelper.delete_dir(downloader.get_store_root())

    def tearDown(self) -> None:
        FileHelper.delete_dir(self.temp_dir)
        downloader = AppPluginDownloader(AppPluginDownloader.REFLEX_COMPONENTS)
        FileHelper.delete_dir(downloader.get_store_root())

    def _fake_download(self, version: str | None = None):
        """Patch FileDownloader.download_file to write a local fake package zip."""
        version = version or AppPluginDownloader.DASHBOARD_COMPONENTS_VERSION
        test = self

        def fake_download_file(downloader_self, url, filename=None, headers=None,
                               timeout=None, destination_folder=None):
            test.download_count += 1
            folder = destination_folder or downloader_self.destination_folder
            return _make_fake_package_zip(folder, version)

        return patch(
            "gws_core.core.classes.file_downloader.FileDownloader.download_file",
            fake_download_file,
        )

    def test_install_store_only(self):
        downloader = AppPluginDownloader(AppPluginDownloader.REFLEX_COMPONENTS)

        with self._fake_download():
            install_path = downloader.install_package()

            self.assertEqual(install_path, downloader.get_version_folder_path())
            self.assertTrue(os.path.exists(os.path.join(install_path, "version.json")))
            self.assertTrue(os.path.exists(os.path.join(install_path, "index.html")))
            self.assertTrue(downloader.is_package_installed())
            self.assertEqual(self.download_count, 1)

            # second call must not download again
            downloader.install_package()
            self.assertEqual(self.download_count, 1)

    def test_install_with_materialize_target(self):
        plugin = _TestPlugin(self.target)

        with self._fake_download():
            install_path = plugin.install_package()

            self.assertEqual(install_path, self.target)
            self.assertTrue(os.path.exists(os.path.join(self.target, "version.json")))
            # the environment file was written in the staging copy, before the swap
            env_file = os.path.join(self.target, "assets", "environment.json")
            self.assertTrue(os.path.exists(env_file))
            with open(env_file, encoding="utf-8") as file:
                env = json.load(file)
            self.assertEqual(env["baseHref"], "external/gws_plugin")
            # no staging leftovers
            parent = os.path.dirname(self.target)
            self.assertEqual([entry for entry in os.listdir(parent) if ".tmp-" in entry], [])

            # a second install is a no-op (no new download, env file refreshed)
            os.remove(env_file)
            with open(env_file, "w", encoding="utf-8") as file:
                file.write("stale")
            plugin.install_package()
            self.assertEqual(self.download_count, 1)
            with open(env_file, encoding="utf-8") as file:
                self.assertNotEqual(file.read(), "stale")

    def test_concurrent_installs_download_once(self):
        """N threads installing concurrently produce one download and a complete store."""
        errors: list[Exception] = []

        def install(index: int):
            try:
                target = os.path.join(self.temp_dir, f"app-{index}", "gws_plugin")
                _TestPlugin(target).install_package()
            except Exception as e:
                errors.append(e)

        with self._fake_download():
            threads = [threading.Thread(target=install, args=(i,)) for i in range(8)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=30)

        self.assertEqual(errors, [])
        # the flock dedupes the store fill: a single download for all callers
        self.assertEqual(self.download_count, 1)
        for i in range(8):
            target = os.path.join(self.temp_dir, f"app-{i}", "gws_plugin")
            self.assertTrue(os.path.exists(os.path.join(target, "version.json")), target)

    def test_bad_version_is_not_installed(self):
        """A package with a wrong version never reaches the store ('exists' == 'complete')."""
        downloader = AppPluginDownloader(AppPluginDownloader.REFLEX_COMPONENTS)

        with (
            self._fake_download(version="dc_0.0.0"),
            self.assertRaisesRegex(Exception, "Failed to download"),
        ):
            downloader.install_package()

        self.assertFalse(os.path.exists(downloader.get_version_folder_path()))
        self.assertFalse(downloader.is_package_installed())

        # a later install retries the download and succeeds
        with self._fake_download():
            downloader.install_package()
        self.assertTrue(downloader.is_package_installed())

    def test_stale_version_replaced_and_old_store_cleaned(self):
        plugin = _TestPlugin(self.target)

        # simulate an old version materialized in the target and present in the store
        FileHelper.create_dir_if_not_exist(self.target)
        with open(os.path.join(self.target, "version.json"), "w", encoding="utf-8") as file:
            json.dump({"version": "dc_0.0.1"}, file)
        old_store_dir = os.path.join(plugin.get_store_root(), "dc_0.0.1")
        FileHelper.create_dir_if_not_exist(old_store_dir)

        with self._fake_download():
            plugin.install_package()

        self.assertTrue(plugin.is_package_installed())
        # old store version garbage collected
        self.assertFalse(os.path.exists(old_store_dir))

    def test_install_from_local_folder_copies_not_moves(self):
        """Dev-mode install must copy the local build (a move consumes the source)."""
        local_source = os.path.join(self.temp_dir, "local-browser")
        FileHelper.create_dir_if_not_exist(os.path.join(local_source, "assets"))
        with open(os.path.join(local_source, "version.json"), "w", encoding="utf-8") as file:
            json.dump({"version": "local"}, file)

        plugin = _TestPlugin(self.target)
        with patch.object(_TestPlugin, "LOCAL_PLUGIN_PATH", local_source):
            plugin._install_from_local_folder()

        self.assertTrue(os.path.exists(os.path.join(self.target, "version.json")))
        # the source is still there for the next app
        self.assertTrue(os.path.exists(os.path.join(local_source, "version.json")))
