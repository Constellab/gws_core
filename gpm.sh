#!/bin/bash

python3 -m pip install GitPython 
python3 -m pip install requests 
python3 -m pip install click 
python3 -m pip install cryptography 

# pull all git repo
python3 gpm.py

# install ubuntu packages
for wks in ".gws" "user"; do
    for path in `find /app/lab/$wks/ -mindepth 1 -maxdepth 4 -name 'requirements-apt.txt'`; do
        cat $path | xargs apt-get install -y
    done
done

# install python dependencies
for wks in ".gws" "user"; do
    for path in `find /app/lab/$wks/ -mindepth 1 -maxdepth 4 -name 'requirements-pip.txt'`; do
        python3 -m pip install -r $path
    done
done

# post-installation hooks
if [ -f /opt/conda/etc/profile.d/conda.sh ]; then
    bash /opt/conda/etc/profile.d/conda.sh
fi

# call custom brick install
for wks in ".gws" "user"; do
    for brick in `find /app/lab/$wks/bricks -mindepth 1 -maxdepth 1 -type d`; do
        if [ -f "$brick/dep/install.py" ]; then
            python3 "$brick/dep/install.py"
        fi

        if [ -f "$brick/dep/install.sh" ]; then
            bash "$brick/dep/install.sh"
        fi
    done
done