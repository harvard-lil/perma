# -*- mode: ruby -*-
# vi: set ft=ruby :
VAGRANTFILE_API_VERSION = "2"

# refer to mysql user by ID because it won't exist yet during provisioning
# note that these may change if the provisioning steps change to create other users first
$MYSQL_UID = 106
$MYSQL_GID = 111

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # ports
  config.vm.network :forwarded_port, guest: 8000, host: 8000 # django dev server
  config.vm.network :forwarded_port, guest: 9000, host: 9000 # nginx server (not started by default)

  # mount mysql folders separately so mysql user can access them
  # (we keep mysql data outside the VM so it persists)
  config.vm.synced_folder "services/mysql/data", "/mysql_data", owner: $MYSQL_UID, group: $MYSQL_GID
  config.vm.synced_folder "services/logs", "/mysql_logs", owner: $MYSQL_UID, group: $MYSQL_GID

  # choose box to use
  # depending on config, we either provision a new box from the base ubuntu distribution,
  # or use a preconfigured box we provisioned and stored online to save time.
  # to provision a new box, call `REGENERATE=1 vagrant up`

  if ENV['REGENERATE']
    # generate our custom build
    puts("regenerating ...")
    config.vm.box = "precise64" # use Ubuntu Precise Pangolin (current Long Term Support release)
    config.vm.box_url = "http://files.vagrantup.com/precise64.box"
    config.vm.provision "shell", path: "services/vagrant/provision.sh"

  else
    puts("using prebuilt perma virtual machine ...")
    config.vm.box = "perma_0.1"
    # TODO: Perma VM is stored on @jcushman's Dropbox. This should be stored somewhere more official.
    config.vm.box_url = "https://dl.dropboxusercontent.com/s/qdvc9hs3lbzaqys/perma_0.1.box"
    config.vm.provision "shell", path: "services/vagrant/provision_mysql.sh"
  end

end
