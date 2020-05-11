
#
# GWS setup
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
#

import os
import sys
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gws-pkg-astro",
    version="0.0.1",
    author="Example Author",
    author_email="admin@gencovery.com",
    description="GWS core package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gencovery.com",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Gencovery License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=[
        'peewe',
        'starlette',
        'uvicorn',
        'aiofiles',
        'jinja2',
        'requests',
        'itsdangerous',
        'awesome-slugify',
        'sqlalchemy'
    ],
)