# -*- mode: ruby -*-
# vi: set ft=ruby :
VAGRANTFILE_API_VERSION = "2"

# refer to mysql user by ID because it won't exist yet during provisioning
# note that these may change if the provisioning steps change to create other users first
$MYSQL_UID = 108
$MYSQL_GID = 113

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # ports
  config.vm.network :forwarded_port, guest: 8000, host: 8000 # django dev server
  config.vm.network :forwarded_port, guest: 9000, host: 9000 # nginx server (not started by default)

  # mount mysql folders separately so mysql user can access them
  # (we keep mysql data outside the VM so it persists)
  config.vm.synced_folder "services/mysql/data", "/mysql_data", owner: $MYSQL_UID, group: $MYSQL_GID
  config.vm.synced_folder "services/logs", "/mysql_logs", owner: $MYSQL_UID, group: $MYSQL_GID

  # tell virtualbox to use a little more RAM
  config.vm.provider "virtualbox" do |v|
    v.memory = 2048
  end

  # choose box to use
  # depending on config, we either provision a new box from the base ubuntu distribution,
  # or use a preconfigured box we provisioned and stored online to save time.

  # To provision a new box:
  # - wipe existing Vagrant/VirtualBox images
  # - REGENERATE=1 vagrant up
  # - REGENERATE=1 vagrant ssh
  # check that new box works as expected
  # - REGENERATE=1 vagrant package --output perma_<box_version>.box
  # - Add new version on atlas.hashicorp.com
  # - set new version below

  if ENV['REGENERATE']
    # generate our custom build
    puts("regenerating ...")
    config.vm.box = "ubuntu/trusty64" # use Ubuntu 14.04 LTS (Trusty Tahr) long-term support version
    # config.vm.box = "precise64" # use Ubuntu Precise Pangolin (current Long Term Support release)
    config.vm.provision "shell", path: "services/vagrant/provision.sh"

  elsif ENV['ANSIBLE']
    config.vm.box = "ubuntu/trusty64" # use Ubuntu 14.04 LTS (Trusty Tahr) long-term support version
    config.vm.provision "ansible" do |ansible|
      ansible.playbook = "services/ansible/playbook.yml"
    end

  else
    puts("using prebuilt perma virtual machine ...")
    config.vm.box = "perma/perma-dev"
    config.vm.box_version = ">= 0.3.0, < 0.4.0"
    config.vm.provision "shell", path: "services/vagrant/provision_mysql.sh"
  end

end
