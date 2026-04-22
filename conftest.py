"""Pytest bootstrap for gws_core tests.

Mirrors what `AppManager.run_test` does when running via `gws server test`:
loads .env.test, initializes the gws environment, connects test DBs. Runs
once per worker process (pytest-xdist spawns one process per worker, so
module-level state stays isolated across workers).
"""

import os
import re
import sys

from dotenv import load_dotenv


TEST_API_BASE_PORT = 3000


def _worker_port_offset() -> int:
    """Return a port offset derived from PYTEST_XDIST_WORKER (gw0 → 0, gw1 → 1, ...)."""
    worker = os.environ.get("PYTEST_XDIST_WORKER") or os.environ.get("GWS_TEST_WORKER_ID", "")
    match = re.search(r"(\d+)$", worker)
    return int(match.group(1)) if match else 0


def _override_api_url_port(env_var: str, port: int) -> None:
    """Rewrite the port in an API URL env var. Leaves host/scheme intact."""
    url = os.environ.get(env_var)
    if not url:
        return
    # Replace any existing :port segment after the host, or append if absent.
    new_url = re.sub(r"(://[^/:]+)(?::\d+)?", rf"\g<1>:{port}", url, count=1)
    os.environ[env_var] = new_url


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

    # Each worker binds its own uvicorn port so integration tests
    # (share scenario, streamlit, reflex) don't fight for port 3000.
    port = TEST_API_BASE_PORT + _worker_port_offset()
    os.environ["GWS_TEST_API_PORT"] = str(port)
    _override_api_url_port("LAB_DEV_API_URL", port)
    _override_api_url_port("LAB_PROD_API_URL", port)

    # Import lazily so dotenv vars are applied before gws_core reads them.
    from gws_core.manage import AppManager
    from gws_core.settings_loader import SettingsLoader

    settings_file = os.path.join(brick_dir, SettingsLoader.SETTINGS_JSON_FILE)
    AppManager.init_gws_env_and_db(
        main_setting_file_path=settings_file,
        log_level="ERROR",
        show_sql=False,
        is_test=True,
    )


_init_gws_env_for_tests()
