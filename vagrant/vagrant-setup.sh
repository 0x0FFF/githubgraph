#!/bin/bash

set -x

# install packages needed to build and run GPDB
sudo yum -y groupinstall "Development tools"
sudo yum -y install python-devel
wget https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py
sudo pip install pg8000 lockfile
rm get-pip.py
sudo yum -y install postgresql-server
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo -i -u postgres createdb vagrant
sudo -i -u postgres createuser -l -s vagrant

# Misc
sudo yum -y install vim mc
