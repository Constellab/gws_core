# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import shutil
import subprocess


def docgen(brick_name, brick_dir, settings, force=False):
    doc_folder = "./docs/"
    gen_folder = "./docs/html/"
    rst_folder = "./rst/"

    try:
        if force:
            try:
                shutil.rmtree(os.path.join(
                    brick_dir, doc_folder), ignore_errors=True)
            except:
                pass

        if not os.path.exists(os.path.join(brick_dir, gen_folder)):
            os.makedirs(os.path.join(brick_dir, gen_folder))

        subprocess.check_call([
            "sphinx-quickstart", "-q",
            f"-p{settings.title}",
            f"-a{settings.authors}",
            f"-v{settings.version}",
            f"-l en",
            "--sep",
            "--ext-autodoc",
            "--ext-todo",
            "--ext-coverage",
            "--ext-mathjax",
            "--ext-ifconfig",
            # "--ext-viewcode",
            "--ext-githubpages",
        ], cwd=os.path.join(brick_dir, gen_folder))

        with open(os.path.join(brick_dir, gen_folder, "./source/conf.py"), "r+") as f:
            content = f.read()
            f.seek(0, 0)
            f.write('\n')
            f.write("import os\n")
            f.write("import sys\n")

            dep_dirs = settings.get_dependency_dirs()
            for k in dep_dirs:
                f.write(f"sys.path.insert(0, '{dep_dirs[k]}')\n")

            f.write("from gws._sphynx import conf\n\n\n")
            f.write(content + '\n')
            f.write("extensions = extensions + conf.extensions\n")
            f.write("exclude_patterns = exclude_patterns + conf.exclude_patterns\n")
            f.write("html_theme = 'sphinx_rtd_theme'")

        subprocess.check_call([
            "sphinx-apidoc",
            "-M",
            f"-H{settings.title}",
            f"-A{settings.authors}",
            f"-V{settings.version}",
            "-f",
            "-o", "./source",
            os.path.join("../../", brick_name)
        ], cwd=os.path.join(brick_dir, gen_folder))

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

                (settings.description or "") + "\n\n" +
                ".. toctree::\n" +
                "   :hidden:\n\n" +
                "   self\n\n" +
                ".. toctree::\n\n" +
                "   intro\n" +
                "   usage\n" +
                "   contrib\n" +
                "   changes\n\n\n" +
                ".. toctree::")

        with open(os.path.join(brick_dir, gen_folder, "./source/index.rst"), "w") as f:
            f.write(content)

        subprocess.check_call([
            "sphinx-build",
            "-b",
            "html",
            "./source",
            "./build",
        ], cwd=os.path.join(brick_dir, gen_folder))

        # if show:
        #    import webbrowser
        #    location = settings.get_dependency_dir(show)
        #    url = os.path.join(location, gen_folder, "./build/index.html")
        #    print(url)
        #    webbrowser.open(f"file://{url}", new=2)

    except Exception as err:

        build_dir = os.path.join(brick_dir, gen_folder, "build")

        if not os.path.exists(build_dir):
            os.makedirs(build_dir)

        file = os.path.join(build_dir, "index.html")
        with open(file, "w") as fp:
            fp.write(
                "No documentation found!"
            )
