
import typer


def main():
    from gws_cli import (brick_cli, dev_env_cli, server_cli, streamlit_cli,
                         task_cli)

    app = typer.Typer(pretty_exceptions_enable=False)
    app.add_typer(server_cli.app, name="server")
    app.add_typer(brick_cli.app, name="brick")
    app.add_typer(task_cli.app, name="task")
    app.add_typer(streamlit_cli.app, name="streamlit")
    app.add_typer(dev_env_cli.app, name="dev-env")

    return app


def enable_logger() -> None:
    from gws_core import Logger, Settings
    log_dir = Settings.build_log_dir(is_test=False)
    Logger(log_dir=log_dir)


def start():
    # load gws_core module before running the app
    from gws_cli.utils.gws_core_loader import load_gws_core

    load_gws_core()
    enable_logger()
    app = main()
    app()


if __name__ == "__main__":
    # import current folder to python path (to make from gws_cli import work)
    import os
    import sys
    path = os.path.join((os.path.abspath(os.path.dirname(__file__))), '..')
    sys.path.append(path)
    start()
