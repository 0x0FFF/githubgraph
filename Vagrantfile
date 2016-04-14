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
