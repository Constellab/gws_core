import json
import os
from typing import Literal

import typer
from gws_core import (
    AppsManager,
    BaseEnvShell,
    CondaShellProxy,
    FileHelper,
    LoggerMessageObserver,
    MambaShellProxy,
    PipShellProxy,
    ShellProxy,
    Utils,
)
from gws_core.apps.app_instance import AppInstance
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.manage import AppManager
from gws_core.user.user import User

from gws_cli.utils.cli_utils import CLIUtils
from gws_cli.utils.dev_config_generator import AppDevConfig

app = typer.Typer()

EnvType = Literal["NONE", "PIP", "CONDA", "MAMBA"]
DEFAULT_CONFIG_FILE_NAME = "dev_config.json"


class AppCli:
    config_file_path: str
    _config: AppDevConfig
    _env_type: EnvType = "NONE"
    _env_file_path: str | None = None

    def __init__(self, config_file_path: str):
        self._load_config(config_file_path)
        self._load_env()
        self._check_resource_ids()

    def _load_config(self, config_file_path: str) -> None:
        if not os.path.isabs(config_file_path):
            config_file_path = os.path.abspath(config_file_path)

        # If the path is a directory, use the default config file in that directory
        if os.path.isdir(config_file_path):
            config_file_path = os.path.join(config_file_path, DEFAULT_CONFIG_FILE_NAME)
            Logger.info(
                f"Provided path is a directory, using default config file: {config_file_path}"
            )

        if not os.path.exists(config_file_path):
            typer.echo(f"Config file '{config_file_path}' does not exist.", err=True)
            raise typer.Abort()

        self.config_file_path = config_file_path

        with open(config_file_path, encoding="UTF-8") as file:
            try:
                config_dict = json.load(file)
                self._config = AppDevConfig.from_json(config_dict)
            except json.JSONDecodeError as e:
                typer.echo(f"Error parsing config file '{config_file_path}': {e}", err=True)
                raise typer.Abort()
            except Exception as e:
                typer.echo(
                    f"Unexpected error reading config file '{config_file_path}': {e}", err=True
                )
                raise typer.Abort()

    def _load_env(self) -> None:
        # Load env_type from config
        env_type: EnvType = self._config.env_type
        if not env_type:
            env_type = "NONE"

        if not Utils.value_is_in_literal(env_type, EnvType):
            typer.echo(
                f"Invalid app type '{env_type}', supported values {Utils.get_literal_values(EnvType)}",
                err=True,
            )
            raise typer.Abort()

        env_file_path = self._config.env_file_path

        if env_type != "NONE":
            if not env_file_path:
                typer.echo(
                    f"Env type is '{env_type}' but the config file '{self.config_file_path}' does not contain 'env_file_path'.",
                    err=True,
                )
                raise typer.Abort()

            # if the app dir path is not absolute (usually on dev mode), make it absolute
            if not os.path.isabs(env_file_path):
                # make the path absolute relative to the config file
                config_file_dir = os.path.dirname(self.config_file_path)
                env_file_path = os.path.join(config_file_dir, env_file_path)
                typer.echo(
                    f"env_file_path is not absolute, making it absolute relative to the config file directory: {config_file_dir}. Absolute path: {env_file_path}"
                )

        self._env_type = env_type
        self._env_file_path = env_file_path

    def _get_shell_proxy(self, env_type: EnvType, env_file_path: str | None) -> ShellProxy:
        if env_type == "NONE":
            return ShellProxy()

        if not env_file_path:
            raise ValueError(f"env_file_path must be provided for env type '{env_type}'")
        if env_type == "PIP":
            return PipShellProxy(env_file_path)
        elif env_type == "CONDA":
            return CondaShellProxy(env_file_path)
        elif env_type == "MAMBA":
            return MambaShellProxy(env_file_path)
        else:
            raise ValueError(f"Invalid env type '{env_type}'")

    def build_shell_proxy(self) -> ShellProxy:
        # create shell and install env if needed
        shell_proxy = self._get_shell_proxy(self._env_type, self._env_file_path)
        shell_proxy.attach_observer(LoggerMessageObserver())
        if isinstance(shell_proxy, BaseEnvShell):
            shell_proxy.install_env()

        return shell_proxy

    def start_app(self, app_: AppInstance, ctx: typer.Context) -> None:
        settings_file_path = CLIUtils.get_current_brick_settings_file_path()

        AppManager.init_gws_env_and_db(
            settings_file_path, log_level=CLIUtils.get_global_option_log_level(ctx)
        )

        AppsManager.init()

        dev_user_email = self._config.dev_user_email
        if dev_user_email:
            user = User.get_by_email_and_check(dev_user_email)
            Logger.info(f"Using dev user '{user.email}'")
            app_.set_dev_user(user.id)

        url = AppsManager.create_or_get_app(app_).get_url()
        is_localhost = Settings.is_local_or_desktop_env()
        additional_message = (
            f"\nPlease make sure the port {Settings.get_app_external_port()} is open."
            if is_localhost
            else ""
        )
        typer.echo(
            "-------------------------------------------------------------------------------------------------------------------------------------"
        )
        env_txt = "" if self._env_type == "NONE" else f" with env type '{self._env_type}'"
        typer.echo(
            f"Running app in dev mode{env_txt}, DO NOT USE IN PRODUCTION. You can access the app at {url}.{additional_message}"
        )
        typer.echo(
            "-------------------------------------------------------------------------------------------------------------------------------------"
        )

    def get_app_dir_path(self) -> str:
        app_dir_path = self._config.app_dir_path
        # if the app dir path is not absolute (usually on dev mode), make it absolute
        if not os.path.isabs(app_dir_path):
            # make the path absolute relative to the config file
            config_file_dir = os.path.dirname(self.config_file_path)
            app_dir_path = os.path.join(config_file_dir, app_dir_path)
            typer.echo(
                f"app_dir_path is not absolute, making it absolute relative to the config file directory: {config_file_dir}. Absolute path: {app_dir_path}"
            )

        if not FileHelper.exists_on_os(app_dir_path):
            typer.echo(f"App directory '{app_dir_path}' does not exist.", err=True)
            raise typer.Abort()

        # Check if the app directory is inside a brick's package folder
        CLIUtils.check_folder_is_in_brick_src(app_dir_path)

        return app_dir_path

    def _check_resource_ids(self) -> None:
        resource_ids = self._config.source_ids
        if not isinstance(resource_ids, list):
            typer.echo(
                f"'source_ids' in config file '{self.config_file_path}' must be a list.", err=True
            )
            raise typer.Abort()

        for resource_id in resource_ids:
            if not isinstance(resource_id, str):
                typer.echo(
                    f"Each resource in 'source_ids' must be a string. Found: {resource_id}",
                    err=True,
                )
                raise typer.Abort()

    def is_reflex_enterprise(self) -> bool:
        return self._config.is_reflex_enterprise
