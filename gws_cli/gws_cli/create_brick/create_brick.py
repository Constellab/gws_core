

import json
import os
import shutil

__cdir__ = os.path.dirname(os.path.abspath(__file__))

skeleton_name = 'brick_skeleton'
user_bricks_folder = '/lab/user/bricks'


def create_brick(name: str):
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


def update_settings_file(dest_dir: str, name: str):
    """ Update settings.json """
    settings_file = os.path.join(dest_dir, "settings.json")
    with open(settings_file, 'r', encoding='UTF-8') as f:
        settings = json.load(f)
        settings["name"] = name
    with open(settings_file, 'w', encoding='UTF-8') as f:
        json.dump(settings, f, indent=4)


def udpate_readme(dest_dir: str, name: str):
    """ Replace all words 'skeleton' in README.md """
    file = os.path.join(dest_dir, "./README.md")
    with open(file, 'r', encoding='UTF-8') as f:
        text = f.read()
        text = text.replace("skeleton", name)
        text = text.replace("Skeleton", name.title())
    with open(file, 'w', encoding='UTF-8') as f:
        f.write(text)


def update_code(dest_dir: str, name: str):
    """ Replace all words 'brick_skeleton' tests imports """
    # rename the test template folder to test_{name}
    template_test_folder = os.path.join(dest_dir, "tests", "test_brick")
    shutil.move(
        template_test_folder,
        os.path.join(dest_dir, "tests", f"test_{name}")
    )

    test_folder = os.path.join(dest_dir, "tests", f"test_{name}")
    file = os.path.join(test_folder, "test_table_factor.py")
    with open(file, 'r', encoding='UTF-8') as f:
        text = f.read()
        text = text.replace(skeleton_name, name)
    with open(file, 'w', encoding='UTF-8') as f:
        f.write(text)
