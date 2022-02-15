# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
import sys
from subprocess import check_call

import setuptools
from setuptools.command.install import install

with open("settings.json", "r", encoding="utf-8") as fh:
    settings = json.load(fh)
    name = settings["name"]
    description = settings["description"]
    version = settings["version"]
    author = settings.get("author", "")
    author_email = settings.get("author_email", "")

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


class InstallHook(install):
    """Installation hooks (for production mode)."""

    def _run_install(self, what):
        cwd = os.path.join(self.install_lib, name)
        script_path = os.path.join(cwd, ".hooks", f"{what}-install.sh")
        if os.path.exists(script_path):
            check_call(["bash", script_path], cwd=cwd)
        script_path = os.path.join(cwd, ".hooks", f"{what}-install.py")
        if os.path.exists(script_path):
            check_call([sys.executable, script_path], cwd=cwd)

    def _run_pre_install(self):
        self.announce("Running pre-install hook ...")
        self._run_install("pre")
        self.announce("Done!")

    def _run_post_install(self):
        self.announce("Running post-install hook ...")
        self._run_install("post")
        self.announce("Done!")

    def run(self):
        self._run_pre_install()
        install.run(self)
        self._run_post_install()


setuptools.setup(
    name=name,
    version=version,
    author=author,
    author_email=author_email,
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    # url="https://github.com/pypa/sampleproject",
    # project_urls={
    #     "Bug Tracker": "https://github.com/pypa/sampleproject/issues",
    # },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.8",
    cmdclass={
        'install': InstallHook,
    },
)
