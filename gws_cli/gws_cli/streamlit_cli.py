
import json
import os

import typer
from typing_extensions import Annotated, Literal

from gws_core import (CondaShellProxy, LoggerMessageObserver, MambaShellProxy,
                      PipShellProxy, ShellProxy, StreamlitApp,
                      StreamlitAppManager, Utils)

app = typer.Typer()

EnvType = Literal['NONE', 'PIP', 'CONDA', 'MAMBA']


def _get_shell_proxy(env_type: EnvType, env_file_path: str) -> ShellProxy:
    if env_type == "NONE":
        return ShellProxy()
    elif env_type == "PIP":
        return PipShellProxy(None, env_file_path)
    elif env_type == "CONDA":
        return CondaShellProxy(None, env_file_path)
    elif env_type == "MAMBA":
        return MambaShellProxy(None, env_file_path)
    else:
        raise ValueError(f"Invalid env type '{env_type}'")


@app.command("run-dev")
def run_dev(config_file_path: Annotated[str, typer.Argument(help="Path of the json config file app to run.")]):

    if not os.path.isabs(config_file_path):
        config_file_path = os.path.abspath(config_file_path)

    if not os.path.exists(config_file_path):
        typer.echo(f"Config file '{config_file_path}' does not exist.", err=True)
        raise typer.Abort()

    dict_: dict = None
    with open(config_file_path, "r", encoding='UTF-8') as file:
        dict_ = json.load(file)

    env_type: EnvType = dict_.get("env_type")
    if not env_type:
        env_type = "NONE"

    if not Utils.value_is_in_literal(env_type, EnvType):
        typer.echo(
            f"Invalid app type '{env_type}', supported values {Utils.get_literal_values(EnvType)}", err=True)
        raise typer.Abort()

    env_file_path = dict_.get("env_file_path")
    if env_type != "NONE":

        if not env_file_path:
            typer.echo(
                f"Env type is '{env_type}' but the config file '{config_file_path}' does not contain 'env_file_path'.",
                err=True)
            raise typer.Abort()

        # if the app dir path is not absolute (usually on dev mode), make it absolute
        if not os.path.isabs(env_file_path):
            # make the path absolute relative to the config file
            config_file_dir = os.path.dirname(config_file_path)
            env_file_path = os.path.join(config_file_dir, env_file_path)
            print(
                f"env_file_path is not absolute, making it absolute relative to the config file directory: {config_file_dir}. Absolute path: {env_file_path}")

    # create shell and install env if needed
    shell_proxy = _get_shell_proxy(env_type, env_file_path)
    shell_proxy.attach_observer(LoggerMessageObserver())
    if (isinstance(shell_proxy, CondaShellProxy)):
        shell_proxy.install_env()

    streamit_app = StreamlitApp("main", shell_proxy)
    streamit_app.set_dev_mode(config_file_path)

    url = StreamlitAppManager.create_or_get_app(streamit_app)
    print("----------------------------------------------------------------------------------------------------------------------------------------------------------")
    print(
        f"Running streamlit in dev mode type '{env_type}', DO NOT USE IN PRODUCTION. You can access the dashboard at {url}")
    print("----------------------------------------------------------------------------------------------------------------------------------------------------------")
