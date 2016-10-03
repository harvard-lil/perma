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
  config.vm.provider "virtualbox" do |v|
    # lazy way to make sure this only runs for "vagrant up"
    if ARGV[0] != "up"
      next
    end

    # default values
    host_cpus = 2
    host_mem = 2048

    # try to get the actual host cpu and ram counts from the vboxmanage command
    begin
      host_info = `vboxmanage list hostinfo`
      host_cpus = /Processor core count: (\d+)/.match(host_info)[1].to_i
      host_mem = /Memory size: (\d+) MByte/.match(host_info)[1].to_i
    rescue Errno::ENOENT
      puts("Warning: vboxmanage command not found. Cannot set optimal ram/cpu.")
    rescue NoMethodError
      puts("Warning: failed to extract ram/cpu counts from `vboxmanage list hostinfo` output. Cannot set optimal ram/cpu.")
    end

    # give guest box 1/4 of memory and cpu count of 1/2 of physical processor cores (as recommended by VirtualBox)
    mem = host_mem/4
    cpus = [1, host_cpus/2].max
    v.memory = mem
    v.cpus = cpus
    
    puts("Using #{mem}MB RAM and #{cpus} CPUs.")
  end
end
