
import json
import os

import typer
from typing_extensions import Annotated

from gws_core import StreamlitApp, StreamlitAppManager, StreamlitAppType, Utils

app = typer.Typer()


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

    app_type: StreamlitAppType = dict_.get("env_type")
    if not app_type:
        app_type = "NORMAL"

    if not Utils.value_is_in_literal(app_type, StreamlitAppType):
        typer.echo(
            f"Invalid app type '{app_type}', supported values {Utils.get_literal_values(StreamlitAppType)}", err=True)
        raise typer.Abort()

    env_file_path = dict_.get("env_file_path")
    if app_type != "NORMAL":

        if not env_file_path:
            typer.echo(
                f"Env type is '{app_type}' but the config file '{config_file_path}' does not contain 'env_file_path'.",
                err=True)
            raise typer.Abort()

        # if the app dir path is not absolute (usually on dev mode), make it absolute
        if not os.path.isabs(env_file_path):
            # make the path absolute relative to the config file
            config_file_dir = os.path.dirname(config_file_path)
            env_file_path = os.path.join(config_file_dir, env_file_path)
            print(
                f"env_file_path is not absolute, making it absolute relative to the config file directory: {config_file_dir}. Absolute path: {env_file_path}")

    streamit_app = StreamlitApp("main", app_type)
    if app_type != "NORMAL" and env_file_path:
        streamit_app.set_env_file_path(env_file_path)
    streamit_app.set_dev_mode(config_file_path)

    url = StreamlitAppManager.create_or_get_app(streamit_app)
    print("----------------------------------------------------------------------------------------------------------------------------------------------------------")
    print(
        f"Running streamlit in dev mode type '{app_type}', DO NOT USE IN PRODUCTION. You can access the dashboard at {url}")
    print("----------------------------------------------------------------------------------------------------------------------------------------------------------")
