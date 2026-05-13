import os
import sys

# Add all brick src/ folders to sys.path BEFORE any gws_core import.
# This mirrors what SettingsLoader.load_brick() does.
BRICKS_DIR = os.path.join(os.environ.get("LAB_FOLDER", "/lab"), "user", "bricks")
for brick_name in os.listdir(BRICKS_DIR):
    src_path = os.path.join(BRICKS_DIR, brick_name, "src")
    if os.path.isdir(src_path) and src_path not in sys.path:
        sys.path.insert(0, src_path)

# Exclude non-test directories from collection (e.g. brick skeleton templates)
collect_ignore_glob = ["**/brick_skeleton/**", "**/gws_cli/**"]


def pytest_configure(config):
    """Called before test collection. Initializes the GWS environment
    so that all brick modules can be imported by test files.
    """
    from gws_core.manage import AppManager

    if AppManager.gws_env_initialized:
        return

    # Determine which brick's settings.json to use as entry point.
    # In dev mode, SettingsLoader auto-discovers all bricks in user brick folder,
    # so using any brick's settings.json loads everything.
    settings_file = os.path.join(BRICKS_DIR, "gws_core", "settings.json")

    # If test path targets a specific brick, use that brick's settings.json
    test_paths = config.args if config.args else []
    for test_path in test_paths:
        abs_path = os.path.abspath(test_path)
        if abs_path.startswith(BRICKS_DIR):
            rel = os.path.relpath(abs_path, BRICKS_DIR)
            brick_name = rel.split(os.sep)[0]
            candidate = os.path.join(BRICKS_DIR, brick_name, "settings.json")
            if os.path.exists(candidate):
                settings_file = candidate
                break

    AppManager.init_gws_env_and_db(
        main_setting_file_path=settings_file,
        log_level="INFO",
        is_test=True,
    )

    # Load .env.test if present
    brick_dir = os.path.dirname(settings_file)
    env_test_file = os.path.join(brick_dir, ".env.test")
    if os.path.exists(env_test_file):
        from dotenv import load_dotenv

        load_dotenv(env_test_file)
