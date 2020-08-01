
#!/bin/bash
# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

python -m pip install --upgrade pip
python -m pip install virtualenv
python -m virtualenv .venv --python=python3

# activate vitual env
. ./.venv/bin/activate

# prism requirement file
python -m pip install -r requirements.txt
