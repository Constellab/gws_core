#!/bin/bash
# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

cd ./docs/ 
sphinx-quickstart

rm ./source/conf.py
cp ./templates/conf.py ./source/
sphinx-apidoc -o ./source ../gws
sphinx-build -b html ./source ./build

cd ../