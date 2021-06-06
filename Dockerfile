FROM "ubuntu:20.04"
LABEL maintainer="Admin <admin@gencovery.com>"

ENV LAB_NAME main
ENV APP_DIR /app
ENV WORKDIR_DIR /app/.gpm
ENV CONDA_VERSION latest

ADD ./ ${WORKDIR_DIR}
WORKDIR ${WORKDIR_DIR}

# install python
RUN apt-get -y update
RUN apt-get -y install python3 python3-distutils
RUN apt-get -y install git curl zip unzip bzip2 wget

# install pip
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3 get-pip.py
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --upgrade setuptools

# install conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-${CONDA_VERSION}-Linux-x86_64.sh -O miniconda.sh && \
    mkdir -p /opt && \
    sh miniconda.sh -b -p /opt/conda && \
    rm miniconda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc
    
# install bazel
RUN apt-get -y install gnupg
RUN curl -fsSL https://bazel.build/bazel-release.pub.gpg | gpg --dearmor > bazel.gpg
RUN mv bazel.gpg /etc/apt/trusted.gpg.d/
RUN echo "deb [arch=amd64] https://storage.googleapis.com/bazel-apt stable jdk1.8" | tee /etc/apt/sources.list.d/bazel.list
RUN apt -y update && apt -y install bazel
RUN apt -y update && apt -y full-upgrade

# install C++ dev tools
RUN apt-get -y install g++ unzip zip
RUN DEBIAN_FRONTEND="noninteractive" apt-get -y install build-essential cmake pkg-config
RUN apt-get -y install libx11-dev libatlas-base-dev
RUN apt-get -y install libgtk-3-dev libboost-python-dev
RUN apt-get -y install libopenblas-dev liblapack-dev

# install R
RUN apt-get -y install r-base

# install jupyter lab
RUN python3 -m pip install jupyterlab
RUN python3 -m pip install ipywidgets

# install code-server for remote vscode
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Create forlder for the vs code config
RUN mkdir -p ${USER}/.local/share/code-server/ && mkdir -p ${USER}/.local/share/code-server/User
# Add config for vs code
COPY ./.vs-code-server-config/settings.json /root/.local/share/code-server/User/settings.json 

# install code-server extensions
# Install jupyter extension
RUN code-server --install-extension ms-toolsai.jupyter
# instal manually python extension version 2020.10.332292344 because higher verison have problem with code-server
# https://github.com/cdr/code-server/issues/2341
RUN wget https://github.com/microsoft/vscode-python/releases/download/2020.10.332292344/ms-python-release.vsix \
 && code-server --install-extension ./ms-python-release.vsix || true

# Install git graph extension
RUN code-server --install-extension mhutchie.git-graph

#EXPOSE 3000

COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]
CMD [ "--runserver" ]
#CMD [ "--runjlab" ]
#CMD [ "--runvlab" ]
