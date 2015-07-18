#!/usr/bin/env python3

import amulet
from pymongo import MongoClient

seconds = 900

d = amulet.Deployment(series='trusty')
d.add('mongodb', charm='mongodb')
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


############################################################
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


validate_world_connectivity()
