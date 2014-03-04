#!/bin/sh

stop mysql

# initialize mysql directory
if [ ! -d /mysql_data/mysql ]; then
  mysql_install_db --user=mysql --datadir=/mysql_data/
  start mysql
  mysqladmin -u root password root
else
  start mysql
fi

# create perma db
if [ ! -d /mysql_data/perma ]; then
  mysql -uroot -proot -e "create database perma character set utf8; grant all on perma.* to perma@'localhost' identified by 'perma';"
fi