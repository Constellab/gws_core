# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import sys
from subprocess import check_call

import setuptools
from setuptools.command.install import install

NAME = "gws_core"
VERSION = "0.2.0"
DESCRIPTION = "Core Gencovery Web Services"
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


class InstallHook(install):
    """Installation hooks (for production mode)."""

    def _run_install(self, what):
        cwd = os.path.join(self.install_lib, NAME)
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
    name=NAME,
    version=VERSION,
    author="Gencovery",
    author_email="admin@gencovery.com",
    description=DESCRIPTION,
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
