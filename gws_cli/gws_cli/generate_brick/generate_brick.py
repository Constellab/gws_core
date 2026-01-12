import json
import os
import shutil

import typer
from gws_core.brick.brick_helper import BrickHelper
from gws_core.brick.brick_settings import (
    BrickSettings,
    BrickSettingsEnvironment,
    BrickSettingsPipSource,
)

__cdir__ = os.path.dirname(os.path.abspath(__file__))

skeleton_name = "brick_skeleton"
user_bricks_folder = "/lab/user/bricks"

DEFAULT_VERSION = "0.1.0"


def generate_brick(name: str):
    name = name.lower().replace(" ", "_").replace("-", "_")

    skeleton_dir = os.path.join(__cdir__, skeleton_name)
    brick_folder = os.path.join(user_bricks_folder, name)

    if os.path.exists(brick_folder):
        typer.echo(
            f"Error: A brick with the name '{name}' already exists at {brick_folder}", err=True
        )
        raise typer.Exit(1)

    shutil.copytree(skeleton_dir, brick_folder, dirs_exist_ok=True)

    # rename the folder inside src to brick name
    shutil.move(
        os.path.join(brick_folder, "src", skeleton_name), os.path.join(brick_folder, "src", name)
    )

    update_settings_file(brick_folder, name)
    update_readme(brick_folder, name)
    update_code(brick_folder, name)
    print(f"The brick {name} was successfully created at {brick_folder}")


def update_settings_file(dest_dir: str, name: str):
    """Create settings.json from BrickSettings object"""
    settings_file = os.path.join(dest_dir, "settings.json")

    # Create environment with empty pip and git packages like the template
    environment = BrickSettingsEnvironment(
        pip=[BrickSettingsPipSource(source="https://pypi.python.org/simple", packages=[])], git=[]
    )

    # Create BrickSettings object
    brick_settings = BrickSettings(
        name=name,
        author="",
        version=DEFAULT_VERSION,
        variables={f"{name}:testdata_dir": "${CURRENT_DIR}/tests/testdata"},
        environment=environment,
    )

    # Add gws_core brick dependency if found
    gws_core_info = BrickHelper.get_brick_info(BrickHelper.GWS_CORE)
    if gws_core_info and gws_core_info.version:
        brick_settings.add_brick_dependency(BrickHelper.GWS_CORE, gws_core_info.version)

    # Write settings.json
    with open(settings_file, "w", encoding="UTF-8") as f:
        json.dump(brick_settings.to_json_dict(), f, indent=2)


def update_readme(dest_dir: str, name: str):
    """Replace all words 'skeleton' in README.md"""
    file = os.path.join(dest_dir, "./README.md")
    with open(file, encoding="UTF-8") as f:
        text = f.read()
        text = text.replace("skeleton", name)
        text = text.replace("Skeleton", name.title())
    with open(file, "w", encoding="UTF-8") as f:
        f.write(text)


def update_code(dest_dir: str, name: str):
    """Replace all words 'brick_skeleton' tests imports"""
    # rename the test template folder to test_{name}
    template_test_folder = os.path.join(dest_dir, "tests", "test_brick")
    shutil.move(template_test_folder, os.path.join(dest_dir, "tests", f"test_{name}"))

    test_folder = os.path.join(dest_dir, "tests", f"test_{name}")
    file = os.path.join(test_folder, "test_table_factor.py")
    with open(file, encoding="UTF-8") as f:
        text = f.read()
        text = text.replace(skeleton_name, name)
    with open(file, "w", encoding="UTF-8") as f:
        f.write(text)
