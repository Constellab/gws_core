import os
import subprocess
import threading
from unittest import TestCase
from unittest.mock import MagicMock, patch

from gws_core.apps.app_nginx_manager import AppNginxManager
from gws_core.apps.app_nginx_service import AppNginxRedirectServiceInfo
from gws_core.core.utils.settings import Settings


def _ok_process() -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=["nginx"], returncode=0, stdout="", stderr="")


def _make_service(service_id: str, port: int) -> AppNginxRedirectServiceInfo:
    return AppNginxRedirectServiceInfo(
        service_id=service_id,
        source_port=8511,
        server_name=f"{service_id}.localhost",
        destination_port=port,
    )


# test_app_nginx_manager
class TestAppNginxManager(TestCase):
    """Atomic nginx config writes + serialized register/reload (issue #103)."""

    manager: AppNginxManager

    def setUp(self) -> None:
        # fresh manager, not the shared singleton
        self.manager = AppNginxManager()

    def test_generate_config_is_atomic(self):
        self.manager._generate_nginx_config()

        config_path = self.manager.get_nginx_config_file_path()
        self.assertTrue(os.path.exists(config_path))
        with open(config_path, encoding="utf-8") as file:
            content = file.read()
        self.assertIn("events {", content)

        # no temp file leftovers next to the config
        config_dir = os.path.dirname(config_path)
        leftovers = [name for name in os.listdir(config_dir) if ".tmp-" in name]
        self.assertEqual(leftovers, [])

    def test_concurrent_register_unregister(self):
        """Concurrent registrations serialize on the lock; the final config is complete."""
        errors: list[Exception] = []
        in_reload = threading.Semaphore(1)

        def fake_run_nginx_command(args):
            # fail the test if two reloads ever overlap
            if not in_reload.acquire(blocking=False):
                errors.append(Exception("nginx command ran concurrently"))
            else:
                in_reload.release()
            return _ok_process()

        def register_and_unregister(index: int):
            try:
                service = _make_service(f"service-{index}", 9000 + index)
                self.manager.register_services([service])
                self.manager.unregister_services([service.service_id])
            except Exception as e:
                errors.append(e)

        with (
            patch.object(self.manager, "_run_nginx_command", side_effect=fake_run_nginx_command),
            patch.object(self.manager, "nginx_is_running", return_value=True),
        ):
            threads = [
                threading.Thread(target=register_and_unregister, args=(i,)) for i in range(10)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=30)

        self.assertEqual(errors, [])
        self.assertEqual(self.manager.get_services(), [])
        # the config on disk is always a complete file
        with open(self.manager.get_nginx_config_file_path(), encoding="utf-8") as file:
            self.assertIn("events {", file.read())

    def test_atexit_registered_once(self):
        with (
            patch.object(self.manager, "_run_nginx_command", return_value=_ok_process()),
            patch.object(self.manager, "nginx_is_running", return_value=False),
            patch("gws_core.apps.app_nginx_manager.atexit.register") as atexit_register,
        ):
            AppNginxManager._atexit_registered = False
            try:
                self.manager.start_or_reload()
                self.manager.start_or_reload()
            finally:
                AppNginxManager._atexit_registered = False

        self.assertEqual(atexit_register.call_count, 1)

    def test_nginx_command_failure_logged_with_output(self):
        failed = subprocess.CompletedProcess(
            args=["nginx"], returncode=1, stdout="", stderr="nginx: [emerg] boom"
        )
        with (
            patch.object(self.manager, "_run_nginx_command", return_value=failed),
            patch("gws_core.apps.app_nginx_manager.Logger.error") as logger_error,
        ):
            self.manager._reload_nginx()

        logged: str = logger_error.call_args[0][0]
        self.assertIn("exit 1", logged)
        self.assertIn("boom", logged)

    def test_run_nginx_command_returns_completed_process(self):
        with patch(
            "gws_core.apps.app_nginx_manager.subprocess.run",
            return_value=_ok_process(),
        ) as run_mock:
            result = self.manager._run_nginx_command(["-t"])

        self.assertIsInstance(result, subprocess.CompletedProcess)
        command: list = run_mock.call_args[0][0]
        self.assertEqual(command[0], "nginx")
        self.assertIn("-t", command)
        self.assertTrue(run_mock.call_args.kwargs["capture_output"])

    def test_external_port_is_test_scoped(self):
        """In test mode the app port band is shifted away from the production port,
        so the test nginx never collides with a real lab nginx on the same machine."""
        base = int(os.environ.get("APP_EXTERNAL_PORT", Settings.APP_EXTERNAL_PORT_DEFAULT))
        expected = (
            base
            + Settings.APP_EXTERNAL_PORT_TEST_OFFSET
            + Settings.get_test_worker_offset() * Settings.APP_EXTERNAL_PORT_WORKER_STRIDE
        )
        self.assertEqual(Settings.get_app_external_port(), expected)
        self.assertNotEqual(Settings.get_app_external_port(), base)

    def test_get_instance_is_singleton(self):
        first = AppNginxManager.get_instance()
        second = AppNginxManager.get_instance()
        self.assertIs(first, second)
        self.assertIsInstance(first, AppNginxManager)
        self.assertIsInstance(first._lock, type(threading.RLock()))

    def test_generate_config_failure_cleans_tmp_file(self):
        with (
            patch.object(
                self.manager, "_build_nginx_config", MagicMock(return_value="content")
            ),
            patch("gws_core.apps.app_nginx_manager.os.replace", side_effect=OSError("disk")),
            self.assertRaisesRegex(Exception, "Failed to write nginx config"),
        ):
            self.manager._generate_nginx_config()

        config_dir = os.path.dirname(self.manager.get_nginx_config_file_path())
        leftovers = [name for name in os.listdir(config_dir) if ".tmp-" in name]
        self.assertEqual(leftovers, [])
