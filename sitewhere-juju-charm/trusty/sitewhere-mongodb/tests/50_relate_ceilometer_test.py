#!/usr/bin/env python3

import amulet


class TestDeploy(object):

    def __init__(self, time=2500):
        # Attempt to load the deployment topology from a bundle.
        self.deploy = amulet.Deployment(series="trusty")

        # If something errored out, attempt to continue by
        # manually specifying a standalone deployment
        self.deploy.add('mongodb')
        self.deploy.add('ceilometer', 'cs:trusty/ceilometer')
        # send blank configs to finalize the objects in the deployment map
        self.deploy.configure('mongodb', {})
        self.deploy.configure('ceilometer', {})

        self.deploy.relate('mongodb:database', 'ceilometer:shared-db')

        try:
            self.deploy.setup(time)
            self.deploy.sentry.wait(time)
        except:
            amulet.raise_status(amulet.FAIL, msg="Environment standup timeout")
        # sentry = self.deploy.sentry

    def run(self):
        for test in dir(self):
            if test.startswith('test_'):
                getattr(self, test)()

    def test_mongo_relation(self):
        unit = self.deploy.sentry.unit['ceilometer/0']
        mongo = self.deploy.sentry.unit['mongodb/0'].info['public-address']
        cont = unit.file_contents('/etc/ceilometer/ceilometer.conf')
        if mongo not in cont:
            amulet.raise_status(amulet.FAIL, "Unable to verify ceilometer cfg")

if __name__ == '__main__':
    runner = TestDeploy()
    runner.run()
