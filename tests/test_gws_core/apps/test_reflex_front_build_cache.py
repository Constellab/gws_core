import os
import threading
from unittest import TestCase

from gws_core.apps.app_nginx_service import AppNginxReflexFrontServerServiceInfo
from gws_core.apps.reflex.reflex_front_build_cache import ReflexFrontBuildCache
from gws_core.apps.reflex.reflex_process import ReflexProcess
from gws_core.core.utils.settings import Settings
from gws_core.impl.apps.reflex_showcase.generate_reflex_showcase_app import ReflexShowcaseApp
from gws_core.impl.file.file_helper import FileHelper


def _make_fake_build(folder: str, content_suffix: str = "") -> None:
    FileHelper.create_dir_if_not_exist(os.path.join(folder, "assets"))
    with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as file:
        file.write(f"<html>{content_suffix}</html>")
    with open(os.path.join(folder, "assets", "reflex-env-abc.js"), "w", encoding="utf-8") as file:
        file.write(f"var e = 'ws://localhost/gws-back/_event'; {content_suffix}")


# test_reflex_front_build_cache
class TestReflexFrontBuildCache(TestCase):
    """Shared frontend build cache + instance-independent build env (issue #103 part B)."""

    cache: ReflexFrontBuildCache

    def setUp(self) -> None:
        self.cache = ReflexFrontBuildCache(ReflexShowcaseApp, ReflexProcess.BACKEND_PATH)
        FileHelper.delete_dir(self.cache.get_app_cache_dir())
        self.temp_dir = Settings.make_temp_dir()

    def tearDown(self) -> None:
        FileHelper.delete_dir(self.cache.get_app_cache_dir())
        FileHelper.delete_dir(self.temp_dir)

    def test_store_and_reuse(self):
        self.assertIsNone(self.cache.get_cached_build_path())

        build_folder = os.path.join(self.temp_dir, "build")
        _make_fake_build(build_folder)

        self.assertTrue(self.cache.store_build(build_folder))
        cached_path = self.cache.get_cached_build_path()
        self.assertEqual(cached_path, self.cache.get_entry_path())
        # entry key contains the brick version
        self.assertIn(str(ReflexShowcaseApp.get_brick_version()), os.path.basename(cached_path))

        # a second instance copies the cached build into its own resource folder
        resource_folder = os.path.join(self.temp_dir, "resource")
        FileHelper.create_dir_if_not_exist(resource_folder)
        self.cache.copy_into(resource_folder)
        self.assertTrue(os.path.exists(os.path.join(resource_folder, "index.html")))
        self.assertTrue(
            os.path.exists(os.path.join(resource_folder, "assets", "reflex-env-abc.js"))
        )
        # no staging leftovers
        leftovers = [
            entry
            for entry in os.listdir(self.cache.get_app_cache_dir())
            if entry.startswith(".tmp-")
        ]
        self.assertEqual(leftovers, [])

    def test_instance_marker_blocks_caching(self):
        """A bundle containing the builder's instance id must not be shared."""
        build_folder = os.path.join(self.temp_dir, "build")
        _make_fake_build(build_folder, content_suffix="app-id-1234")

        self.assertFalse(self.cache.store_build(build_folder, instance_marker="app-id-1234"))
        self.assertIsNone(self.cache.get_cached_build_path())

        # a clean bundle with the same marker configured is cached
        clean_folder = os.path.join(self.temp_dir, "clean")
        _make_fake_build(clean_folder)
        self.assertTrue(self.cache.store_build(clean_folder, instance_marker="app-id-1234"))
        self.assertIsNotNone(self.cache.get_cached_build_path())

    def test_stale_entries_are_cleaned(self):
        stale_entry = os.path.join(self.cache.get_app_cache_dir(), "0.0.1--deadbeef")
        FileHelper.create_dir_if_not_exist(stale_entry)

        build_folder = os.path.join(self.temp_dir, "build")
        _make_fake_build(build_folder)
        self.cache.store_build(build_folder)

        self.assertFalse(os.path.exists(stale_entry))
        self.assertIsNotNone(self.cache.get_cached_build_path())

    def test_concurrent_store_keeps_one_complete_entry(self):
        errors: list[Exception] = []

        def store(index: int):
            try:
                build_folder = os.path.join(self.temp_dir, f"build-{index}")
                _make_fake_build(build_folder)
                self.cache.store_build(build_folder)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=store, args=(i,)) for i in range(6)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

        self.assertEqual(errors, [])
        self.assertIsNotNone(self.cache.get_cached_build_path())

    def test_build_env_is_instance_independent(self):
        """The export env must not contain the instance's backend host."""
        process = ReflexProcess.__new__(ReflexProcess)
        runtime_env = {
            "GWS_REFLEX_API_URL": "http://my-instance-id-back.localhost:8510",
            "GWS_APP_ID": "my-instance-id",
        }
        build_env = process._get_build_env(runtime_env)

        self.assertEqual(
            build_env["GWS_REFLEX_API_URL"],
            f"http://localhost:{Settings.get_app_external_port()}",
        )
        self.assertEqual(build_env["REFLEX_BACKEND_PATH"], ReflexProcess.BACKEND_PATH)
        self.assertEqual(build_env[ReflexProcess.BUILD_MODE_ENV_VAR], "1")
        # the runtime env is untouched (backend keeps serving at root with the -back URL)
        self.assertNotIn("REFLEX_BACKEND_PATH", runtime_env)
        self.assertEqual(
            runtime_env["GWS_REFLEX_API_URL"], "http://my-instance-id-back.localhost:8510"
        )

    def test_front_nginx_block_proxies_backend_prefix(self):
        service = AppNginxReflexFrontServerServiceInfo(
            service_id="my-app-front",
            source_port=9510,
            server_name="my-app.localhost",
            front_folder_path="/data/build",
            backend_port=8536,
            backend_path=ReflexProcess.BACKEND_PATH,
        )
        config = service.get_nginx_service_config()

        # ^~ prefix location wins over the regex asset location; trailing slash strips the prefix
        self.assertIn(f"location ^~ {ReflexProcess.BACKEND_PATH}/", config)
        self.assertIn("proxy_pass http://127.0.0.1:8536/;", config)
        self.assertIn('proxy_set_header Connection "upgrade";', config)
        # the backend location must be rendered before the asset regex location
        self.assertLess(
            config.index(f"location ^~ {ReflexProcess.BACKEND_PATH}/"),
            config.index("location ~*"),
        )

        # without backend info the block is unchanged (old behavior)
        legacy = AppNginxReflexFrontServerServiceInfo(
            service_id="my-app-front",
            source_port=9510,
            server_name="my-app.localhost",
            front_folder_path="/data/build",
        )
        self.assertNotIn("location ^~", legacy.get_nginx_service_config())
