
import typer
from typing_extensions import Annotated

from gws_cli.app_cli import AppCli
from gws_cli.generate_streamlit_app.generate_streamlit_app import \
    generate_streamlit_app
from gws_core import StreamlitApp

app = typer.Typer()


@app.command("run-dev")
def run_dev(config_file_path: Annotated[str, typer.Argument(help="Path of the json config file app to run.")]):

    app_cli = AppCli(config_file_path)
    shell_proxy = app_cli.build_shell_proxy()

    streamit_app = StreamlitApp("main", "main", shell_proxy)
    streamit_app.set_dev_mode(config_file_path)

    app_cli.start_app(streamit_app)


@app.command("generate")
def generate(
        name: Annotated[str, typer.Argument(help="Name of the streamlit app (snake_case).")]):
    print(f"Generating streamlit app: '{name}'")
    app_folder = generate_streamlit_app(name)
    print(f"Streamlit app '{name}' created successfully in '{app_folder}'.")
