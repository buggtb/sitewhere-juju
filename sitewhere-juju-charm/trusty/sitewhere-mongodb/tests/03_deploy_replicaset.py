#!/usr/bin/env python3

import amulet
import requests
import time
from pymongo import MongoClient
from collections import Counter


#########################################################
# Test Quick Config
#########################################################
scale = 3
seconds = 1800

# amount of time to wait before testing for replicaset
# status
wait_for_replicaset = 15

#########################################################
# 3shard cluster configuration
#########################################################
d = amulet.Deployment(series='trusty')

d.add('mongodb', charm='mongodb', units=scale)
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
    'mongodb2-sentry': d.sentry.unit['mongodb/2'],
}


#############################################################
# Check presence of MongoDB GUI HEALTH Status
#############################################################
def validate_status_interface():
    r = requests.get("http://{}:28017".format(
        d.sentry.unit['mongodb/0'].info['public-address']),
        verify=False)
    r.raise_for_status


#############################################################
# Validate that each unit has an active mongo service
#############################################################
def validate_running_services():
    for service in sentry_dict:
        output = sentry_dict[service].run('service mongodb status')
        service_active = str(output).find('mongodb start/running')
        if service_active == -1:
            message = "Failed to find running MongoDB on host {}".format(
                service)
            amulet.raise_status(amulet.SKIP, msg=message)


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
    if secondrs != 2:
        message = "Only two SECONDARY units allowed! (Found %s)" % (secondrs)
        amulet.raise_status(amulet.FAIL, message)


#############################################################
# Validate connectivity from $WORLD
#############################################################
def validate_world_connectivity():
    client = MongoClient(d.sentry.unit['mongodb/0'].info['public-address'])

    db = client['test']
    # Can we successfully insert?
    insert_id = db.amulet.insert({'assert': True})
    if insert_id is None:
        amulet.raise_status(amulet.FAIL, msg="Failed to insert test data")
    # Can we delete from a shard using the Mongos hub?
    result = db.amulet.remove(insert_id)
    if result['err'] is not None:
        amulet.raise_status(amulet.FAIL, msg="Failed to remove test data")


validate_status_interface()
validate_running_services()
validate_replicaset_setup()
validate_world_connectivity()
