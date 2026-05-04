"""Pytest bootstrap for gws_core tests.

Mirrors what `AppManager.run_test` does when running via `gws server test`:
loads .env.test, initializes the gws environment, connects test DBs. Runs
once per worker process (pytest-xdist spawns one process per worker, so
module-level state stays isolated across workers).
"""

import os
import sys

from dotenv import load_dotenv

TEST_API_BASE_PORT = 3000


def _force_local_api_url(env_var: str, port: int) -> None:
    """Pin an API URL env var to http://localhost:<port>.

    Tests spawn a local uvicorn (see TestStartUvicornApp); any code that
    builds URLs from these env vars (share links, get_current_lab_route,
    ResourceDownloaderHttp, etc.) must hit that local server, not the
    real public hostname configured in .env.test.
    """
    os.environ[env_var] = f"http://localhost:{port}"


def _init_gws_env_for_tests() -> None:
    brick_dir = os.path.dirname(os.path.abspath(__file__))

    # Make gws_core importable for pytest workers even when the CLI wrapper
    # didn't set up sys.path (e.g. when invoking pytest directly).
    src_dir = os.path.join(brick_dir, "src")
    if os.path.isdir(src_dir) and src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    env_test_file = os.path.join(brick_dir, ".env.test")
    if os.path.exists(env_test_file):
        load_dotenv(env_test_file)

    # Import lazily so dotenv vars are applied before gws_core reads them.
    from gws_core.core.utils.settings import Settings
    from gws_core.manage import AppManager
    from gws_core.settings_loader import SettingsLoader

    # Each worker binds its own uvicorn port so integration tests
    # (share scenario, streamlit, reflex) don't fight for port 3000.
    port = TEST_API_BASE_PORT + Settings.get_test_worker_offset()
    os.environ["GWS_TEST_API_PORT"] = str(port)
    _force_local_api_url("LAB_DEV_API_URL", port)
    _force_local_api_url("LAB_PROD_API_URL", port)

    # Force LOCAL so ShareLink.is_lab_share_resource_link accepts the
    # localhost URLs above; otherwise the share-resource downloader
    # silently falls back to DirectUrlResourceDownloader.
    os.environ["LAB_ENVIRONMENT"] = "LOCAL"

    settings_file = os.path.join(brick_dir, SettingsLoader.SETTINGS_JSON_FILE)
    AppManager.init_gws_env_and_db(
        main_setting_file_path=settings_file,
        log_level=os.environ.get("GWS_TEST_LOG_LEVEL", "ERROR"),
        show_sql=False,
        is_test=True,
    )


_init_gws_env_for_tests()
