
import os
import subprocess

import typer
from typing_extensions import Annotated

from gws_core import BrickService

app = typer.Typer()


@app.command("run-dev")
def run_dev(config_file_path: Annotated[str, typer.Argument(help="Path of the json config file app to run.")]):

    gws_core_path = BrickService.get_brick_src_folder("gws_core")
    main_app_path = os.path.join(gws_core_path, 'streamlit/_main_streamlit_app.py')

    if not os.path.isabs(config_file_path):
        config_file_path = os.path.abspath(config_file_path)

    if not os.path.exists(config_file_path):
        typer.echo(f"Config file '{config_file_path}' does not exist.", err=True)
        raise typer.Abort()

    subprocess.run([
        "streamlit",
        "run",
        main_app_path,
        "--server.port", "8501",
        "--server.allowRunOnSave", "true",
        "--",
        "--dev_mode", "true",
        "--dev_config_file", config_file_path
    ], check=False)