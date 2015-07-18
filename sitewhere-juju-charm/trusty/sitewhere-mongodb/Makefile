# This file is part of the mongodb charm.
# Copyright (C) 2013 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License version 3, as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranties of MERCHANTABILITY,
# SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

PYTHON := /usr/bin/env python

clean:
	rm -f .coverage
	find . -name '*.pyc' -delete
	rm -rf .venv
	(which dh_clean && dh_clean) || true

.venv:
	sudo apt-get install -y gcc python-dev python-virtualenv python-apt
	virtualenv .venv --system-site-packages
	.venv/bin/pip install -I -r test_requirements.txt

lint:   .venv
	.venv/bin/flake8 --exclude hooks/charmhelpers hooks tests unit_tests

test:  .venv
	@echo Starting unit tests...
	.venv/bin/nosetests -s --nologcapture --with-coverage $(EXTRA) unit_tests/

functional_test:
	@echo Starting amulet tests...
	@juju test -v -p AMULET_HTTP_PROXY --timeout 900

sync:
	@mkdir -p bin
	@bzr cat lp:charm-helpers/tools/charm_helpers_sync/charm_helpers_sync.py > bin/charm_helpers_sync.py
	@$(PYTHON) bin/charm_helpers_sync.py -c charm-helpers-sync.yaml

publish: lint unit_test
	bzr push lp:charms/mongodb
	bzr push lp:charms/trusty/mongodb
