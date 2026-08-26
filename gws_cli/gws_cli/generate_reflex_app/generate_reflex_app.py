import os
import shutil

import typer
from gws_core import FileHelper, ShellProxy

from gws_cli.utils.app_env_generator import (
    build_env_template_vars,
    copy_env_file,
    validate_env_type,
)
from gws_cli.utils.app_generator import AppGenerator
from gws_cli.utils.cli_utils import CLIUtils
from gws_cli.utils.dev_config_generator import create_dev_config_json
from gws_cli.utils.typer_message_observer import TyperMessageObserver

APP_NAME_VAR = "APP_NAME"

TEMPLATE_FOLDER = os.path.join(os.path.dirname(__file__), "_template")
TEMPLATE_ENV_FOLDER = os.path.join(os.path.dirname(__file__), "_template_env")
# App code files specific to virtual environment apps, they override the default app code
TEMPLATE_ENV_APP_OVERLAY_FOLDER = os.path.join(TEMPLATE_ENV_FOLDER, "app_overlay")
GENERATE_APP_TEMPLATE_NAME = "generate_app_template.txt"
REFLEX_MAIN_FILE = "reflex_main.py"
ASSETS_FOLDER = "assets"


def _generate_reflex_app_task(snake_case_name: str, app_folder: str, env_type: str) -> None:
    """Generate the ``generate_<name>.py`` task file from the reflex generate template.

    :param snake_case_name: The snake_case name of the app
    :param app_folder: The path to the app folder where the task file is created
    :param env_type: Virtual environment type ("NONE", "PIP", "CONDA" or "MAMBA")
    """
    template_path = os.path.join(TEMPLATE_FOLDER, GENERATE_APP_TEMPLATE_NAME)
    generate_task_path = os.path.join(app_folder, f"generate_{snake_case_name}.py")
    shutil.copy2(template_path, generate_task_path)

    # Replace the common app variables (app class names, folder name, ...)
    AppGenerator.replace_vars_in_file(snake_case_name, generate_task_path, "reflex")

    # Replace the env specific variables
    CLIUtils.replace_vars_in_file(
        generate_task_path,
        build_env_template_vars("reflex", env_type, snake_case_name),
    )


def _run_reflex_init(name: str, snake_case_name: str, reflex_app_folder: str) -> None:
    """Run the ``reflex init`` command to generate the base Reflex app.

    :param name: The original name of the app, used in the progress message
    :param snake_case_name: The snake_case name of the app, passed to ``reflex init``
    :param reflex_app_folder: The folder in which the reflex app is generated
    :raises typer.Abort: if the reflex init command fails
    """
    typer.echo(f"Generating Reflex app '{name}'...")
    shell = ShellProxy(working_dir=reflex_app_folder)
    shell.attach_observer(TyperMessageObserver())
    result = shell.run(
        ["reflex", "init", "--name", snake_case_name, "--template", "blank"],
        dispatch_stdout=True,
        dispatch_stderr=True,
    )

    if result != 0:
        typer.echo(
            f"Failed to generate Reflex app. Command 'reflex init --name {snake_case_name}' returned {result}",
            err=True,
        )
        raise typer.Abort()


def generate_reflex_app(name: str, is_enterprise: bool, env_type: str = "NONE") -> str:
    """Method to create a new reflex app with the given name.

    :param name: name of the reflex app
    :type name: str
    :param is_enterprise: whether to generate an enterprise Reflex app
    :type is_enterprise: bool
    :param env_type: virtual environment to run the app in. One of "NONE", "PIP",
        "CONDA" or "MAMBA". Defaults to "NONE".
    :type env_type: str
    :raises ValueError: if the env type is not supported
    :return: path to the created reflex app
    :rtype: str
    """
    env_type = validate_env_type(env_type)
    # Validate app name and check if folder already exists
    current_folder = os.getcwd()
    snake_case_name = AppGenerator.validate_app_name_and_folder(name, current_folder)

    # The folder where the app will be created
    app_folder = os.path.join(current_folder, snake_case_name)

    # create the app folder
    FileHelper.create_dir_if_not_exist(app_folder)

    reflex_app_folder = os.path.join(app_folder, "_" + snake_case_name)
    FileHelper.create_dir_if_not_exist(reflex_app_folder)

    try:
        # Run the reflex init command to generate the base app
        _run_reflex_init(name, snake_case_name, reflex_app_folder)

        # Replace the rxconfig.py file with our template
        template_rxconfig_path = os.path.join(TEMPLATE_FOLDER, "rxconfig.py")
        app_rxconfig_path = os.path.join(reflex_app_folder, "rxconfig.py")

        if not FileHelper.exists_on_os(app_rxconfig_path):
            typer.echo(f"Expected rxconfig.py not found at '{app_rxconfig_path}'", err=True)
            raise typer.Abort()
        # Replace the rxconfig.py with our template

        shutil.copy2(template_rxconfig_path, app_rxconfig_path)

        # Replace the APP_NAME variable in rxconfig.py
        replace_variables = {APP_NAME_VAR: snake_case_name}
        CLIUtils.replace_vars_in_file(app_rxconfig_path, replace_variables)

        # Copy the env file inside the app code folder when a virtual env is requested
        dev_env_file_path = ""
        if env_type != "NONE":
            dev_env_file_path = copy_env_file(
                TEMPLATE_ENV_FOLDER, "reflex", env_type, reflex_app_folder
            )

        # Create the dev_config.json file
        create_dev_config_json(
            reflex_app_folder,
            is_reflex_enterprise=is_enterprise,
            env_type=env_type,
            env_file_path=dev_env_file_path,
        )

        # Copy the reflex_main.py file, override the default one. A virtual env app
        # cannot load gws_core, so it uses the env variant which imports from
        # gws_reflex_env_main instead.
        if env_type != "NONE":
            reflex_main_template_path = os.path.join(
                TEMPLATE_ENV_APP_OVERLAY_FOLDER, REFLEX_MAIN_FILE
            )
        else:
            reflex_main_template_path = os.path.join(TEMPLATE_FOLDER, REFLEX_MAIN_FILE)
        app_reflex_main_path = os.path.join(
            reflex_app_folder, snake_case_name, snake_case_name + ".py"
        )
        shutil.copy2(reflex_main_template_path, app_reflex_main_path)

        # add "uploaded_files/" to the .gitignore file
        gitignore_path = os.path.join(reflex_app_folder, ".gitignore")
        if FileHelper.exists_on_os(gitignore_path):
            with open(gitignore_path, "a", encoding="utf-8") as gitignore_file:
                gitignore_file.write("uploaded_files/\n")
        else:
            typer.echo(f"Expected .gitignore not found at '{gitignore_path}'", err=True)
            raise typer.Abort()

        # Create the generate task file, injecting the virtual env if requested
        _generate_reflex_app_task(snake_case_name, app_folder, env_type)

        # Copy the CSS file into assets folder
        assets_folder = os.path.join(reflex_app_folder, ASSETS_FOLDER)
        FileHelper.create_dir_if_not_exist(assets_folder)
        source_assets_folder = os.path.join(TEMPLATE_FOLDER, ASSETS_FOLDER)
        FileHelper.copy_dir_content_to_dir(source_assets_folder, assets_folder)

        typer.echo(f"Successfully created Reflex app at '{reflex_app_folder}'")
        return reflex_app_folder

    except Exception as e:
        # Clean up if something went wrong
        if FileHelper.exists_on_os(app_folder):
            shutil.rmtree(app_folder)
        typer.echo(f"Error generating Reflex app: {str(e)}", err=True)
        raise e
