# stuff run when the vagrant user logs in

# for virtualenvwrapper
# put virtualenvs in /vagrant so they can be inspected by PyCharm running on host computer
export WORKON_HOME=/home/vagrant/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh

# start celery
# TODO: celery is automatically started on boot, so this shouldn't be necessary, but for some reason it fails at that point
sudo start celery >> ~/.service_log 2>&1 &

# mysql seems to be running-but-not-running after boot
# TODO: fix mysql boot
( (sudo stop mysql >> ~/.service_log 2>&1; sudo start mysql >> ~/.service_log 2>&1) &)

# prepare for Django work
workon perma
cd /vagrant/perma_web