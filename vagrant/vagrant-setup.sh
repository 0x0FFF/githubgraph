#!/bin/bash

# Copyright 2016 Alexey Grishchenko
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
