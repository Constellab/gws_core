
import typer


def main():
    from gws_cli import (brick_cli, dev_env_cli, reflex_cli, server_cli,
                         streamlit_cli, task_cli)

    app = typer.Typer(
        pretty_exceptions_enable=False,
        help="GWS CLI - Command line interface for managing applications, bricks, and development environment.",
        context_settings={"help_option_names": ["-h", "--help"]}
    )

    app.add_typer(server_cli.app, name="server",
                  help="Manage server operations (run, test, execute scenarios/processes)")
    app.add_typer(brick_cli.app, name="brick", help="Generate and manage bricks")
    app.add_typer(task_cli.app, name="task", help="Generate task classes")
    app.add_typer(streamlit_cli.app, name="streamlit", help="Generate and run Streamlit applications")
    app.add_typer(reflex_cli.app, name="reflex", help="Generate and run Reflex applications")
    app.add_typer(dev_env_cli.app, name="dev-env", help="Manage development environment (reset data)")

    return app


def enable_logger() -> None:
    from gws_core import Logger, Settings
    log_dir = Settings.build_log_dir(is_test=False)
    Logger.build_main_logger(log_dir=log_dir)


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
