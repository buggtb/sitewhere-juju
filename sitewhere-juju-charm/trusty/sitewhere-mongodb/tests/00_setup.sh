#!/bin/bash

set -e

sudo apt-get install python-setuptools -y
sudo add-apt-repository ppa:juju/stable -y

sudo apt-get update
sudo apt-get install amulet python3 python3-requests python3-pymongo juju-core charm-tools python-mock python-pymongo -y
