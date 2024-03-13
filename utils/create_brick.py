

import json
import os
import shutil

import click

__cdir__ = os.path.dirname(os.path.abspath(__file__))

skeleton_name = 'brick_skeleton'
user_bricks_folder = '/lab/user/bricks'


@click.command(context_settings=dict(
    ignore_unknown_options=False,
    allow_extra_args=False
))
@click.pass_context
@click.option('--name', '-n', help='Brick name')
def main(ctx, name=None, desc=None):
    name = name.lower().replace(" ", "_").replace("-", "_")

    skeleton_dir = os.path.join(__cdir__, skeleton_name)
    brick_folder = os.path.join(user_bricks_folder, name)

    if os.path.exists(brick_folder):
        raise Exception("A brick with the same name already exist")

    shutil.copytree(
        skeleton_dir,
        brick_folder,
        dirs_exist_ok=True
    )

    # rename the folder inside src to brick name
    shutil.move(
        os.path.join(brick_folder, "src", skeleton_name),
        os.path.join(brick_folder, "src", name)
    )

    update_settings_file(brick_folder, name)
    udpate_readme(brick_folder, name)
    update_code(brick_folder, name)
    print(f"The brick {name} was successfully created.")


def update_settings_file(dest_dir, name):
    """ Update settings.json """
    settings_file = os.path.join(dest_dir, "settings.json")
    with open(settings_file, 'r') as f:
        settings = json.load(f)
        settings["name"] = name
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=4)


def udpate_readme(dest_dir, name):
    """ Replace all words 'skeleton' in README.md """
    file = os.path.join(dest_dir, "./README.md")
    with open(file, 'r') as f:
        text = f.read()
        text = text.replace("skeleton", name)
        text = text.replace("Skeleton", name.title())
    with open(file, 'w') as f:
        f.write(text)


def update_code(dest_dir, name):
    """ Replace all words 'brick_skeleton' tests imports """
    file = os.path.join(dest_dir, "tests", "test_table_factor.py")
    with open(file, 'r') as f:
        text = f.read()
        text = text.replace(skeleton_name, name)
    with open(file, 'w') as f:
        f.write(text)


if __name__ == "__main__":
    main()
