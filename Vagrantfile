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

# IP Address for the private VM network
ip_address = "192.168.10.199"

# Basic Vagrant config (API version 2)
Vagrant.configure(2) do |config|

  # Base box: Centos-7 box
  config.vm.box = "boxcutter/centos72"

  # Make this VM reachable on the host network as well, so that other
  # VM's running other browsers can access our dev server.
  config.vm.network :private_network, ip: ip_address
  config.vm.network :forwarded_port, guest: 22, host: 2223

  # Give a reasonable amount of cpu and memory to the VM
  config.vm.provider "virtualbox" do |vb|
    vb.name = "githubgraph-vm" # Name in VirtualBox
    vb.memory = 4096
    vb.cpus = 2
  end

  # Make the GPDB code folder will be visible as /gpdb in the virtual machine
  config.vm.synced_folder ".", "/data"

  # Install packages that are needed to build and run GPDB
  config.vm.provision "shell", path: "vagrant/vagrant-setup.sh"
  config.vm.provision "shell", path: "vagrant/vagrant-configure-os.sh", args: ip_address

end
