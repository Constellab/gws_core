import os
from typing import Dict

import typer
from gws_core import BrickService, Logger
from gws_core.settings_loader import SettingsLoader


class CLIUtils:
    MAIN_SETTINGS_FILE_DEFAULT_PATH = "/lab/.sys/app/settings.json"

    @staticmethod
    def get_global_option_log_level(ctx: typer.Context) -> str:
        """Get the global log level option from the context.

        :param ctx: Typer context
        :type ctx: typer.Context
        :return: Log level
        :rtype: str
        """
        return ctx.obj["log_level"]

    @staticmethod
    def replace_vars_in_file(file_path: str, variables: Dict[str, str]):
        """Method to replace the variables in a file.
        The variables are formatted as {{var_name}} in the file.

        :param file_path: path to the file
        :type file_path: str
        :param vars: dictionary of variables to replace
        :type vars: Dict[str, str]
        """
        with open(file_path, "r", encoding="UTF-8") as f:
            text = f.read()

            for key, value in variables.items():
                text = CLIUtils.replace_variable(text, key, value)

        with open(file_path, "w", encoding="UTF-8") as f:
            f.write(text)

    @staticmethod
    def replace_variable(text: str, var_name: str, value: str) -> str:
        # variable are formatted as {{var_name}}
        text = text.replace("{{" + var_name + "}}", value)
        return text

    @staticmethod
    def get_current_brick_dir() -> str | None:
        """Get the current brick dir, if the current dir is not inside a brick, return None.

        :return: path to the brick dir or None
        :rtype: str | None
        """
        return BrickService.get_parent_brick_folder(os.getcwd())

    @staticmethod
    def get_and_check_current_brick_dir() -> str:
        """Get the current brick dir, if the current dir is not inside a brick, return None.

        :return: path to the brick dir or None
        :rtype: str | None
        """
        brick_dir = CLIUtils.get_current_brick_dir()
        if not brick_dir:
            typer.echo(
                "The current folder is not inside a brick, please run the command inside a brick folder or provide the brick name.",
                err=True,
            )
            raise typer.Abort()

        return brick_dir

    @staticmethod
    def get_current_brick_settings_file_path() -> str:
        """Get the current brick settings file path, if the current dir is not inside a brick, return None.

        :return: path to the brick settings file or None
        :rtype: str | None
        """
        brick_dir = CLIUtils.get_current_brick_dir()

        if not brick_dir:
            Logger.info(
                f"Command not run inside a brick folder, using the default main settings file path: '{CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH}'"
            )

            if not os.path.exists(CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH):
                typer.echo(
                    f"Default main settings file '{CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH}' does not exist.",
                    err=True,
                )
                raise typer.Abort()

            return CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH

        settings_file_path = os.path.join(brick_dir, SettingsLoader.SETTINGS_JSON_FILE)
        if not os.path.exists(settings_file_path):
            typer.echo(f"'settings.json' file not found in the brick '{brick_dir}'.", err=True)
            raise typer.Abort()

        return settings_file_path
