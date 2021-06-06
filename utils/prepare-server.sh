#!/bin/bash

sudo apt-get -y update

sudo apt-get -y install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

sudo apt-key fingerprint 0EBFCD88

sudo add-apt-repository -y \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

sudo apt-get -y update
sudo apt-get -y install docker-ce docker-ce-cli containerd.io
sudo apt-get -y install docker-compose

sudo usermod -aG docker $USER

# mount /dev/sbd disk
sudo bash ./mount/mount.sh

# Detect GPU and install
if [[ "$distribution" == "$max_distribution_for_gpu" ]] || [[ "$distribution" < "$max_distribution_for_gpu" ]]; then
    if [ "`lspci | grep -i nvidia`" != "" ]; then
        sudo bash ./gpu/install-cuda.sh
        sudo systemctl restart docker
    fi
fi


sudo reboot
