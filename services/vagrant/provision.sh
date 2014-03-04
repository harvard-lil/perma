#!/bin/sh

### set up vagrant user ###
echo '. "/vagrant/services/vagrant/profile.sh"' >> /home/vagrant/.profile

### hosts ###
printf "\n\n127.0.0.1 perma.dev\n127.0.0.1 users.perma.dev" >> /etc/hosts

### basic packages ###
apt-get -y update
apt-get install -y git build-essential

### install mysql ###
debconf-set-selections <<< 'mysql-server mysql-server/root_password password root'                                      # set root password to 'root'
debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password root'
apt-get -y install mysql-server libmysqlclient-dev                                                                      # install package
ln -sf /vagrant/services/mysql/apparmor_conf /etc/apparmor.d/local/usr.sbin.mysqld                                      # hook up apparmor settings file so mysql can access our paths
sudo invoke-rc.d apparmor reload
ln -sf /vagrant/services/mysql/my.cnf /etc/mysql/                                                                       # hook up settings file
restart mysql

### create perma database ###
mysql -uroot -proot -e "create database perma character set utf8;" &&
    mysql -uroot -proot -e "grant all on perma.* to perma@'localhost' identified by 'perma';"

### install Python packages ###
apt-get install -y python-dev                                                                                           # for stuff that compiles from source
apt-get install -y libffi-dev                                                                                           # dependency for cryptography
sudo apt-get install -y libxml2-dev libxslt1-dev                                                                        # dependencies for lxml
apt-get install -y python-pip
pip install --upgrade pip virtualenvwrapper
export WORKON_HOME=/home/vagrant/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
mkvirtualenv perma
workon perma
pip install --upgrade distribute # dependency for mysql
pip install -r /vagrant/perma_web/requirements.txt

### install task queue (rabbitmq and celery) ###
apt-get install -y rabbitmq-server
cp /vagrant/services/celery/celery.conf /etc/init/celery.conf
start celery

### install nginx and uwsgi ###
# these are disabled by default
apt-get install -y nginx-full uwsgi
ln -s /vagrant/services/nginx/nginx.conf /etc/nginx/sites-enabled/
ln -s /vagrant/services/uwsgi/perma.ini /etc/uwsgi/apps-enabled/
cp /vagrant/services/uwsgi/uwsgi.conf /etc/init/uwsgi.conf
#service nginx start
#service uwsgi start

### install phantomjs ###
# have to download manually since the apt-get phantomjs is currently back at version 1.4
apt-get install -y fontconfig
cd /usr/local/share
wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-1.9.7-linux-x86_64.tar.bz2
tar xjf phantomjs-1.9.7-linux-x86_64.tar.bz2
ln -s /usr/local/share/phantomjs-1.9.7-linux-x86_64/bin/phantomjs /usr/bin/
rm phantomjs-1.9.7-linux-x86_64.tar.bz2

### clean up permissions ###
chown -R vagrant /home/vagrant/.virtualenvs