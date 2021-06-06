#!/bin/bash

# install cuda driver
# https://developer.nvidia.com/cuda-downloads?target_os=Linux&target_arch=x86_64&target_distro=Ubuntu&target_version=2004&target_type=debnetwork

sudo apt-get update && apt-get install -y wget
sudo apt-get install -y gnupg2
sudo apt-get -y install software-properties-common
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub
sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
sudo apt-get update
DEBIAN_FRONTEND="noninteractive"
sudo apt-get -y install cuda

# install NVIDIA toolkit
# https://developer.nvidia.com/cuda-downloads?target_os=Linux&target_arch=x86_64&target_distro=Ubuntu&target_version=2004&target_type=debnetwork

sudo curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
sudo curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && apt-get install -y nvidia-docker2

# set nvidia runtime
# https://www.jbnet.fr/systeme/docker/docker-configurer-lutilisation-du-gpu-nvidia.html
# https://docs.nvidia.com/dgx/nvidia-container-runtime-upgrade/index.html

sudo apt-get install -y jq
sudo cp /etc/docker/daemon.json /etc/docker/daemon.gws-bkp.json
sudo jq '. + { "default-runtime": "nvidia" }' /etc/docker/daemon.json > daemon.json
sudo mv daemon.json /etc/docker/daemon.json
