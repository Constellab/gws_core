from typing import Annotated

import typer
from gws_core import StreamlitApp

from gws_cli.app_cli import AppCli
from gws_cli.generate_streamlit_app.generate_streamlit_app import generate_streamlit_app

app = typer.Typer(help="Generate and run Streamlit applications")


@app.command("run", help="Run a Streamlit app in development mode")
def run_dev(
    ctx: typer.Context,
    config_file_path: Annotated[
        str, typer.Argument(help="Path to the JSON config file for the app to run.")
    ],
    enable_debugger: Annotated[
        bool,
        typer.Option(
            "--enable-debugger", help="Enable the debugger in the Streamlit app.", is_flag=True
        ),
    ] = False,
):
    app_cli = AppCli(config_file_path)
    shell_proxy = app_cli.build_shell_proxy()

    streamit_app = StreamlitApp(StreamlitApp.DEV_MODE_APP_ID, "main", shell_proxy)
    streamit_app.set_dev_mode(config_file_path)
    streamit_app.set_enable_debugger(enable_debugger)

    app_cli.start_app(streamit_app, ctx)


@app.command("generate", help="Generate a new Streamlit app")
def generate(name: Annotated[str, typer.Argument(help="Name of the Streamlit app (snake_case).")]):
    print(f"Generating streamlit app: '{name}'")
    app_folder = generate_streamlit_app(name)
    print(f"Streamlit app '{name}' created successfully in '{app_folder}'.")
