#!/usr/bin/env python3

import amulet
import time
from pymongo import MongoClient
from collections import Counter


#########################################################
# Test Quick Config
#########################################################
scale = 2
seconds = 1800

# amount of time to wait before testing for replicaset
# status
wait_for_replicaset = 30
# amount of time to wait for the data relation
wait_for_relation = 60*2

#########################################################
# 3shard cluster configuration
#########################################################
d = amulet.Deployment(series='trusty')

d.add('mongodb', units=scale, series='trusty')
d.add('storage', charm='cs:~chris-gondolin/trusty/storage-5', series='trusty')
d.configure('storage', {'provider': 'local'})

d.expose('mongodb')

# Perform the setup for the deployment.
try:
    d.setup(seconds)
    d.sentry.wait(seconds)
except amulet.helpers.TimeoutError:
    message = 'The environment did not setup in %d seconds.', seconds
    amulet.raise_status(amulet.SKIP, msg=message)
except:
    raise

sentry_dict = {
    'mongodb0-sentry': d.sentry.unit['mongodb/0'],
    'mongodb1-sentry': d.sentry.unit['mongodb/1'],
}


#############################################################
# Check agent status
#############################################################
def validate_status():
    d.sentry.wait_for_status(d.juju_env, ['mongodb'])


#############################################################
# Validate proper replicaset setup
#############################################################
def validate_replicaset_setup():

    time.sleep(wait_for_replicaset)

    unit_status = []

    for service in sentry_dict:
        client = MongoClient(sentry_dict[service].info['public-address'])
        r = client.admin.command('replSetGetStatus')
        unit_status.append(r['myState'])
        client.close()

    primaries = Counter(unit_status)[1]
    if primaries != 1:
        message = "Only one PRIMARY unit allowed! Found: %s" % (primaries)
        amulet.raise_status(amulet.FAIL, message)

    secondrs = Counter(unit_status)[2]
    if secondrs != 1:
        message = "Only one SECONDARY unit allowed! (Found %s)" % (secondrs)
        amulet.raise_status(amulet.FAIL, message)


validate_status()
validate_replicaset_setup()
print("Adding storage relation, and sleeping for 2 min.")
d.relate('mongodb:data', 'storage:data')
time.sleep(wait_for_relation)
validate_status()
validate_replicaset_setup()
