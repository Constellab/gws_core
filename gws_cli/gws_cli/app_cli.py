
import json
import os

import typer
from typing_extensions import Literal

from gws_core import (AppsManager, BaseEnvShell, CondaShellProxy, FileHelper,
                      LoggerMessageObserver, MambaShellProxy, PipShellProxy,
                      ShellProxy, Utils)
from gws_core.apps.app_instance import AppInstance

app = typer.Typer()

EnvType = Literal['NONE', 'PIP', 'CONDA', 'MAMBA']


class AppCli:

    _config_file_path: str = None
    _config: dict = None
    _env_type: EnvType = "NONE"
    _env_file_path: str | None = None

    def __init__(self, config_file_path: str):
        self._config_file_path = config_file_path
        self._load_config(config_file_path)
        self._load_env()
        self._check_resource_ids()

    def _load_config(self, config_file_path: str) -> None:
        if not os.path.isabs(config_file_path):
            config_file_path = os.path.abspath(config_file_path)

        if not os.path.exists(config_file_path):
            typer.echo(f"Config file '{config_file_path}' does not exist.", err=True)
            raise typer.Abort()

        with open(config_file_path, "r", encoding='UTF-8') as file:
            self._config = json.load(file)

    def _load_env(self) -> None:
        # Load env_type from config
        env_type: EnvType = self._config.get("env_type")
        if not env_type:
            env_type = "NONE"

        if not Utils.value_is_in_literal(env_type, EnvType):
            typer.echo(
                f"Invalid app type '{env_type}', supported values {Utils.get_literal_values(EnvType)}", err=True)
            raise typer.Abort()

        env_file_path = self._config.get("env_file_path")

        if env_type != "NONE":

            if not env_file_path:
                typer.echo(
                    f"Env type is '{env_type}' but the config file '{self._config_file_path}' does not contain 'env_file_path'.",
                    err=True)
                raise typer.Abort()

            # if the app dir path is not absolute (usually on dev mode), make it absolute
            if not os.path.isabs(env_file_path):
                # make the path absolute relative to the config file
                config_file_dir = os.path.dirname(self._config_file_path)
                env_file_path = os.path.join(config_file_dir, env_file_path)
                print(
                    f"env_file_path is not absolute, making it absolute relative to the config file directory: {config_file_dir}. Absolute path: {env_file_path}")

        self._env_type = env_type
        self._env_file_path = env_file_path

    def _get_shell_proxy(self, env_type: EnvType, env_file_path: str | None) -> ShellProxy:
        if env_type == "NONE":
            return ShellProxy()
        elif env_type == "PIP":
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

    def start_app(self, app_: AppInstance) -> None:

        url = AppsManager.create_or_get_app(app_).get_url()
        print("-------------------------------------------------------------------------------------------------------------------------------------")
        env_txt = "" if self._env_type == "NONE" else f" with env type '{self._env_type}'"
        print(
            f"Running app in dev mode{env_txt}, DO NOT USE IN PRODUCTION. You can access the dashboard at {url}")
        print("-------------------------------------------------------------------------------------------------------------------------------------")

    def get_app_dir_path(self) -> str:
        if 'app_dir_path' not in self._config:
            typer.echo(f"Config file '{self._config_file_path}' does not contain 'app_dir_path'.", err=True)
            raise typer.Abort()

        app_dir_path = self._config.get("app_dir_path")
        # if the app dir path is not absolute (usually on dev mode), make it absolute
        if not os.path.isabs(app_dir_path):
            # make the path absolute relative to the config file
            config_file_dir = os.path.dirname(self._config_file_path)
            app_dir_path = os.path.join(config_file_dir, app_dir_path)
            print(
                f"app_dir_path is not absolute, making it absolute relative to the config file directory: {config_file_dir}. Absolute path: {app_dir_path}")

        if not FileHelper.exists_on_os(app_dir_path):
            typer.echo(f"App directory '{app_dir_path}' does not exist.", err=True)
            raise typer.Abort()

        return app_dir_path

    def _check_resource_ids(self) -> None:
        if 'source_ids' not in self._config:
            typer.echo(f"Config file '{self._config_file_path}' does not contain 'source_ids'.", err=True)
            raise typer.Abort()

        resource_ids = self._config.get("source_ids")
        if not isinstance(resource_ids, list):
            typer.echo(f"'resources' in config file '{self._config_file_path}' must be a list.", err=True)
            raise typer.Abort()

        for resource_id in resource_ids:
            if not isinstance(resource_id, str):
                typer.echo(f"Each resource in 'resources' must be a string. Found: {resource_id}", err=True)
                raise typer.Abort()
