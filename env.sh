
#!/bin/bash
# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

python3 -m pip install --upgrade pip
python3 -m pip install virtualenv
python3 -m virtualenv .venv --python=python3

# activate vitual env
. ./.venv/bin/activate

# prism requirement file
for req in "$@"
do
  python3 -m pip install -r "$req"
done

