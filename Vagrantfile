# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure("2") do |config|

  config.vm.box = "perma/perma-dev"
  config.vm.box_version = "~> 1.0"
  config.vm.hostname = "perma"
  config.vm.network :forwarded_port, guest: 8000, host: 8000 # django dev server
  config.vm.network :forwarded_port, guest: 9000, host: 9000 # nginx server (not started by default)
  config.vm.network :forwarded_port, guest: 8080, host: 8080 # jasmine
  config.vm.synced_folder ".", "/vagrant"

  # configure CPU/RAM
  # via https://stefanwrobel.com/how-to-make-vagrant-performance-not-suck
  config.vm.provider "virtualbox" do |v|
    host = RbConfig::CONFIG['host_os']

    # Give VM 1/4 system memory & access to all cpu cores on the host
    if host =~ /darwin/
      cpus = `sysctl -n hw.ncpu`.to_i
      # sysctl returns Bytes and we need to convert to MB
      mem = `sysctl -n hw.memsize`.to_i / 1024 / 1024 / 4
    elsif host =~ /linux/
      cpus = `nproc`.to_i
      # meminfo shows KB and we need to convert to MB
      mem = `grep 'MemTotal' /proc/meminfo | sed -e 's/MemTotal://' -e 's/ kB//'`.to_i / 1024 / 4
    else # TODO: cpu/ram detection for Windows
      cpus = 2
      mem = 1024
    end

    v.memory = mem
    v.cpus = cpus
    puts("Using #{mem}MB RAM and #{cpus} CPUs.")
  end
end
