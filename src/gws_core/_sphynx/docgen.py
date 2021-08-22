# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import shutil
import subprocess
from typing import List
from ..core.utils.utils import Utils

class Docgen:

    @staticmethod
    def generate(settings, force=False):
        doc_folder = "./docs/"
        gen_folder = "./docs/html/"
        rst_folder = "./rst/"
        brick_dir  = settings.get_cwd()
        try:
            if force:
                try:
                    shutil.rmtree(os.path.join(
                        brick_dir, doc_folder), ignore_errors=True)
                except:
                    pass
            if not os.path.exists(os.path.join(brick_dir, gen_folder)):
                os.makedirs(os.path.join(brick_dir, gen_folder))
            subprocess.check_call(
                [
                    "sphinx-quickstart", "-q",
                    f"-p{settings.name}",
                    f"-a{settings.author}",
                    f"-v{settings.version}",
                    "-l en",
                    "--sep",
                    "--ext-autodoc",
                    "--ext-todo",
                    "--ext-coverage",
                    "--ext-mathjax",
                    "--ext-ifconfig",
                    # "--ext-viewcode",
                    "--ext-githubpages",
                ],
                cwd=os.path.join(brick_dir, gen_folder)
            )
            with open(os.path.join(brick_dir, gen_folder, "./source/conf.py"), "r+") as f:
                content = f.read()
                f.seek(0, 0)
                f.write('\n')
                f.write("import os\n")
                f.write("import sys\n")
                f.write("import sphinx_rtd_theme\n")
                brick_paths: List[str] = Utils.get_all_brick_paths()
                for path in brick_paths:
                    f.write(f"sys.path.insert(0, '{path}')\n")
                f.write(content + '\n')
                f.write("extensions = ['sphinx_rtd_theme','rinoh.frontend.sphinx']\n")
                f.write("exclude_patterns = ['settings.py','manage.py']\n")
                f.write("html_theme = 'sphinx_rtd_theme'")
            subprocess.check_call(
                [
                    "sphinx-apidoc",
                    "-M",
                    f"-H{settings.name}",
                    f"-A{settings.author}",
                    f"-V{settings.version}",
                    "-f",
                    "-o", "./source",
                    brick_dir #os.path.join("../../", brick_name)
                ],
                cwd=os.path.join(brick_dir, gen_folder)
            )
            for f in ['intro.rst', 'usage.rst', 'contrib.rst', 'changes.rst']:
                if os.path.exists(os.path.join(brick_dir, rst_folder, f)):
                    shutil.copyfile(
                        os.path.join(brick_dir, rst_folder, f),
                        os.path.join(brick_dir, gen_folder, "./source/"+f))

            # insert modules in index
            with open(os.path.join(brick_dir, gen_folder, "./source/index.rst"), "r") as f:
                content = f.read()
                content = content.replace(
                    ":caption: Contents:",
                    ":caption: API documentation:\n\n   modules\n\n")
                content = content.replace(
                    ".. toctree::",
                    #(description or "") +
                    ".. toctree::\n\n" +
                    "   intro\n" +
                    "   usage\n" +
                    "   contrib\n" +
                    "   changes\n\n\n" +
                    ".. toctree::")
            with open(os.path.join(brick_dir, gen_folder, "./source/index.rst"), "w") as f:
                f.write(content)
            subprocess.check_call(
                [
                    "sphinx-build",
                    "-b",
                    "html",
                    "./source",
                    "./build",
                ],
                cwd=os.path.join(brick_dir, gen_folder)
            )
        except Exception as err:
            build_dir = os.path.join(brick_dir, gen_folder, "build")
            if not os.path.exists(build_dir):
                os.makedirs(build_dir)
            file = os.path.join(build_dir, "index.html")
            with open(file, "w") as fp:
                fp.write("An error occured when generating the documentation.")

            raise err
