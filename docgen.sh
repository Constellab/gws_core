cd ./docs/ 
sphinx-quickstart

rm ./source/conf.py
cp ./templates/conf.py ./source/
sphinx-apidoc -o ./source ../gws
sphinx-build -b html ./source ./build

cd ../