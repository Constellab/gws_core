import json
import os
import tempfile

from gws_core.apps.reflex.reflex_app import ReflexApp
from gws_core.apps.reflex.reflex_plugin import ReflexPlugin
from gws_core.apps.reflex.reflex_process import ReflexProcess
from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.utils.execution_context import ExecutionContext
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.shell.shell_proxy import ShellProxy


class ReflexCompiler:
    """Compile a Reflex app without starting it, to check that it builds.

    ``reflex compile`` imports the app modules (``rxconfig.py``, the states, the pages),
    so it surfaces syntax errors, bad imports and invalid component usage. But a bare
    ``reflex compile`` fails on a gws Reflex app: the app code imports ``gws_reflex_base`` /
    ``gws_reflex_main``, which are only reachable through the ``PYTHONPATH`` that
    :class:`~gws_core.apps.reflex.reflex_process.ReflexProcess` sets on the app process, and
    the state code reads several ``GWS_*`` environment variables at import time.

    This class rebuilds just that environment, without any of the runtime machinery
    (no port allocation, no nginx service, no backend process, no health check).

    The compile runs in **build mode** (``GWS_REFLEX_BUILD_MODE=1``), the same mode
    ``reflex export`` uses, so the state code bakes neutral values instead of requiring a
    real app id or an authenticated user.

    Build mode alone is not enough: ``reflex compile`` prerenders the pages, which evaluates
    the ``@rx.var`` computed vars, and those read the app config file. So a throwaway app
    config is written to a temp file for the duration of the compile, carrying the params
    from the app instance and no user token. This is why the compile needs **no database and
    no lab environment** — the only thing being checked is that the app code compiles.

    Because the compile evaluates computed vars against a config with no resources and no
    authenticated user, a *successful* compile proves the app builds, not that it runs
    correctly with real data.
    """

    # Sentinel app id used for the compile. Mirrors the build-mode app id, since the
    # compile runs in build mode and no real app instance exists.
    COMPILE_APP_ID = "gws-compile"

    _app: ReflexApp
    _shell_proxy: ShellProxy
    # Path of the throwaway app config, set for the duration of the compile
    _app_config_path: str | None = None

    def __init__(self, app: ReflexApp, shell_proxy: ShellProxy):
        """
        :param app: the Reflex app to compile. Its app folder must be set (via
            ``set_app_static_folder`` or ``set_app_config``).
        :type app: ReflexApp
        :param shell_proxy: the shell used to run the ``reflex`` command. Pass an env shell
            proxy (pip/conda/mamba) for a virtual environment app.
        :type shell_proxy: ShellProxy
        """
        self._app = app
        self._shell_proxy = shell_proxy

    def compile(self, dry: bool = True) -> int:
        """Compile the app and return the exit code of the ``reflex compile`` command.

        :param dry: if True, run ``reflex compile --dry``, which compiles without writing
            the generated frontend to disk. Set to False to keep the generated ``.web``
            output, defaults to True
        :type dry: bool, optional
        :return: the exit code of the command, 0 on success
        :rtype: int
        """
        app_folder = self._app.get_app_folder()
        if not app_folder:
            raise Exception(
                "The app folder is not set. Please call `set_app_config` or "
                "`set_app_static_folder` before compiling the app."
            )

        main_file_path = os.path.join(app_folder, ReflexApp.MAIN_FILE_NAME)
        if not os.path.exists(main_file_path):
            raise Exception(
                f"'{ReflexApp.MAIN_FILE_NAME}' not found in '{app_folder}'. "
                "This folder does not look like a Reflex app."
            )

        self._shell_proxy.working_dir = app_folder

        # Materialize the gws_plugin in the app folder before the compile imports the
        # gws components, so it is not downloaded from inside the reflex process.
        ReflexPlugin(app_folder).install_package()

        cmd = [
            "reflex",
            "compile",
            f"--loglevel={self._get_log_level().lower()}",
        ]
        if dry:
            cmd.append("--dry")

        with tempfile.TemporaryDirectory(prefix="gws_reflex_compile_") as temp_dir:
            self._app_config_path = self._write_temp_app_config(temp_dir)
            env = self.get_compile_env()

            # Log the equivalent manual command, to allow debugging the compile by hand
            env_str_cmd = " ".join(f"{key}={value}" for key, value in env.items())
            Logger.debug(f"Command to compile the app: {env_str_cmd} {' '.join(cmd)}")

            return self._shell_proxy.run(
                cmd, env=env, dispatch_stdout=True, dispatch_stderr=True
            )

    def _write_temp_app_config(self, temp_dir: str) -> str:
        """Write the throwaway app config read by the state during the compile.

        Mirrors the ``ReflexConfigDTO`` shape the running app would get, minus anything that
        needs the lab: no resource is loaded (``source_ids`` is empty even when the app
        instance has some, since resolving them requires the database) and no user token is
        provisioned, so the compile never authenticates.

        :param temp_dir: folder the config is written into
        :type temp_dir: str
        :return: path of the written config file
        :rtype: str
        """
        config = {
            "source_ids": [],
            "params": self._app.params or {},
            "user_access_tokens": {},
        }

        config_path = os.path.join(temp_dir, "app_config.json")
        with open(config_path, "w", encoding="utf-8") as file:
            json.dump(config, file)

        return config_path

    def get_compile_env(self) -> dict[str, str]:
        """Build the environment variables needed to compile the app.

        Mirrors :meth:`ReflexProcess._get_base_env` for the values read at import time, but
        uses neutral placeholders for everything that is instance-specific: build mode makes
        those values unused by the compiled output.

        :return: the environment variables for the ``reflex compile`` command
        :rtype: dict[str, str]
        """
        env_dict = {
            "PYTHONPATH": self._get_python_path(),
            ExecutionContext.get_os_env_name(): ExecutionContext.REFLEX.value,
            # Build mode: the state code bakes neutral values (no app id, no auth info)
            # instead of raising on the missing instance environment.
            ReflexProcess.BUILD_MODE_ENV_VAR: "1",
            ReflexProcess.APP_ID_ENV_VAR: self.COMPILE_APP_ID,
            # Read by the state when the compile prerenders the pages and evaluates the
            # computed vars. Points at the throwaway config written for this compile.
            "GWS_APP_CONFIG_FILE_PATH": self._app_config_path or "",
            "GWS_IS_VIRTUAL_ENV": str(self._app.is_virtual_env_app()),
            "GWS_IS_DEV_MODE": str(self._app.is_dev_mode()),
            "GWS_IS_TEST_ENV": str(Settings.get_instance().is_test),
            "GWS_APP_ACCESS_MODE": self._app.access_mode.value,
            "GWS_LOG_LEVEL": self._get_log_level(),
            # No backend is started for a compile, so these URLs are never called. They are
            # still set because the app code reads them at import time.
            "GWS_LAB_API_URL": Settings.get_lab_api_url(),
            "GWS_REFLEX_API_URL": f"http://localhost:{Settings.get_app_external_port()}",
            "REFLEX_BACKEND_PATH": ReflexProcess.BACKEND_PATH,
        }

        # Enterprise components are resolved at compile time, so the token is required to
        # compile an enterprise app. Only Settings is used (no SpaceService call), to keep
        # the compile runnable without a lab environment.
        if self._app.is_enterprise():
            access_token = Settings.get_reflex_access_token()
            if not access_token:
                raise Exception(
                    "This is an enterprise Reflex app but no reflex access token is configured. "
                    "Set the reflex access token in the lab settings to compile it."
                )
            env_dict["REFLEX_ACCESS_TOKEN"] = access_token

        return env_dict

    def _get_log_level(self) -> str:
        """The current gws Logger level, or INFO when no logger is initialized.

        The compile can run standalone (no lab environment), in which case the Logger
        singleton does not exist, so reading its level must never break the compile.
        """
        try:
            return Logger.get_instance().level
        except Exception:
            return "INFO"

    def _get_python_path(self) -> str:
        """PYTHONPATH exposing gws_reflex_base / gws_reflex_main, plus gws_core for
        non virtual environment apps (which import it directly)."""
        reflex_modules_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), ReflexProcess.REFLEX_MODULES_PATH
        )
        if not os.path.exists(reflex_modules_path):
            raise Exception(f"Reflex modules not found at {reflex_modules_path}")

        python_path = reflex_modules_path

        if not self._app.is_virtual_env_app():
            brick_info = BrickHelper.get_brick_info_and_check(BrickHelper.GWS_CORE)
            python_path += ":" + brick_info.get_python_module_path()

        return python_path
