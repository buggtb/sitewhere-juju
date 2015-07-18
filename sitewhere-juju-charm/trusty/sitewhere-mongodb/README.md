# Overview

This charm deploys [MongoDB](http://mongodb.org) in three configurations:

- Single node
- Replica set
- Sharded clusters

By default, the MongoDB application is installed from the Ubuntu archive, except for arm64 platforms. The version of MongoDB in the archive is known to have issues on arm64, so by default this charm will use ppa:mongodb-arm64/ppa which contains backported fixes for this architecture.

# Usage

## Review the configurable options

The MongoDB charm allows for certain values to be configurable via a config.yaml file. The options provided are extensive, you should [review the options](https://jujucharms.com/fullscreen/search/precise/mongodb-20/?text=mongodb#bws-configuration).

Specifically the following options are important:

- replicaset
   - ie: myreplicaset
   - Each replicaset has a unique name to distinguish it’s members from other replicasets available in the network.
   - The default value of "myset" should be fine for most single cluster scenarios.

- web_admin_ui
   - MongoDB comes with a basic but very informative web user interface that provides health
     and status information on the database node as well as the cluster.
   - The default value of yes will start the Admin web UI on port 28017.

Most of the options in config.yaml have been modeled after the default configuration file for mongodb (normally in /etc/mongodb.conf) and should be familiar to most mongodb admins.  Each option in this charm have a brief description of what it does.

# Usage

## Single Node

Deploy the first MongoDB instance

    juju deploy mongodb
    juju expose mongodb

## Replica Sets

### Deploying

Deploy the first two MongoDB instances that will form replicaset:

    juju deploy mongodb -n 2

Deploying three or more units at start can sometimes lead to unexpected race-conditions so it's best to start with two nodes.

Your deployment should look similar to this ( `juju status` ):

    environment: amazon
    machines:
      "0":
        agent-state: started
        agent-version: 1.16.5
        dns-name: ec2-184-73-7-172.compute-1.amazonaws.com
        instance-id: i-cb55cceb
        instance-state: running
        series: precise
        hardware: arch=amd64 cpu-cores=1 cpu-power=100 mem=1740M root-disk=8192M
      "1":
        agent-state: pending
        dns-name: ec2-54-196-181-161.compute-1.amazonaws.com
        instance-id: i-974bd2b7
        instance-state: pending
        series: precise
        hardware: arch=amd64 cpu-cores=1 cpu-power=100 mem=1740M root-disk=8192M
    services:
      mongodb:
        charm: cs:precise/mongodb-20
        exposed: false
        relations:
          replica-set:
          - mongodb
        units:
          mongodb/0:
            agent-state: pending
            machine: "1"
            public-address: ec2-54-196-181-161.compute-1.amazonaws.com


In addition, the MongoDB web interface should also be accessible via the services’
public-address and port 28017 ( ie: http://ec2-50-17-73-255.compute-1.amazonaws.com:28017 ).

### (Optional) Change the replicaset name

    juju set mongodb replicaset=<new_replicaset_name>

### Add one or more nodes to your replicaset

    juju add-unit mongodb
    juju add-unit mongodb -n2

We now have a working MongoDB replica-set.

### Caveats

Keep in mind that you need to have odd number of nodes for a properly formed replicaset.

Replicaset can't function with only one available node - shall this happens the remaining node is switched to 'read-only' until at least one of the broken nodes is restored.

More info can be found in MongoDB documentation at [their website](http://docs.mongodb.org/manual/replication/)

### Removing a failed node

Working units can be removed from replica set using 'juju remove-unit' command. If the removing unit is primary it will automatically be stepped down (so thath re-election of new primary is performend) before being removed.
However, if a unit fails (freezes, gets destroyed and is unbootable), operator needs to manually remove it. The operator would connect to primary unit, and issue rs.remove() for failed unit. Also, operator needs to issue 'juju remove-unit --force' to remove failed unit from juju.

### Recovering from degraded replicaset

If two members go down replicaset is in read-only state. That is because the
remaining node is in SECONDARY state (it can't get promoted/voted to PRIMARY
because there is no majority in replicaset). If failed nodes can't be brought
back to life we need to manually force remaining node to become a primary. Here
is how:

 1. connect to the node that's alive
 2. start 'mongo', a cli utility
 3. upon connecting you'll see that node is SECONDARY
 4. display current configuration with:
      rs.config()
      - this will show the alive node as well as the nodes that are unreachabble

 5. store the configuration into some temporary json document:
      cfg=rs.config()

 6. change the cfg document so that it's members array contain only the unit
    that is alive:
      cfg.members=[cfg.members[0]]

 7. force reconfiguration of the replicaset:
      rs.reconfigure(cfg, {force: true})

 8. wait a few, and press ENTER. You should see that your node becomes PRIMARY.

After this clean up the unavailable machines from juju:
       juju remove-machine --force XX    ## XX is the machine number

And add more units to form a proper replicaset. (To avoid race conditions it is
best to add units one by one).

       juju add-unit mongodb

## Sharding (Scale Out Usage)

According the the MongoDB documentation found on [their website](http://docs.mongodb.org/manual/tutorial/deploy-shard-cluster/), one way of deploying a Shard Cluster is as follows:

- deploy config servers
- deploy a mongo shell (mongos)
- deploy shards
- connect the config servers to the mongo shell
- add the shards to the mongo shell

Using Juju we can deploy a sharded cluster using the following commands:

### Prepare a configuration file similar to the following:

    shard1:
      replicaset: shard1
    shard2:
      replicaset: shard2
    shard3:
      replicaset: shard3
    configsvr:
      replicaset: configsvr

We'll save this one as `~/mongodb-shard.yaml`.

### Bootstrap the environment
    juju bootstrap

### Config Servers ( we'll deploy 3 of them )
    juju deploy mongodb configsvr --config ~/mongodb-shard.yaml -n3

### Mongo Shell ( We just deploy one for now )
    juju deploy mongodb mongos

### Shards ( We'll deploy three replica-sets )
    juju deploy mongodb shard1 --config ~/mongodb-shard.yaml -n3
    juju deploy mongodb shard2 --config ~/mongodb-shard.yaml -n3
    juju deploy mongodb shard3 --config ~/mongodb-shard.yaml -n3

### Connect the Config Servers to the Mongo shell (mongos)

    juju add-relation mongos:mongos-cfg configsvr:configsvr

### Connect each Shard to the Mongo shell (mongos)

    juju add-relation mongos:mongos shard1:database
    juju add-relation mongos:mongos shard2:database
    juju add-relation mongos:mongos shard3:database

With the above commands, we should now have a three replica-set sharded cluster running.
Using the default configuration, here are some details of our sharded cluster:

- mongos is running on port 27021
- configsvr is running on port 27019
- the shards are running on the default mongodb port of 27017
- The web admin is turned on by default and accessible with your browser on port 28017 on each of the shards.

To verify that your sharded cluster is running, connect to the mongo shell and run `sh.status()`:

- `mongo --host <mongos_host>:<mongos_port>`
- `run sh.status()`
You should see your the hosts for your shards in the status output.

### Use the storage subordinate to store mongodb data on a permanent OpenStack or Amazon EBS volume

The [storage](http://manage.jujucharms.com/charms/precise/storage) subordinate and [block-storage-broker](http://manage.jujucharms.com/charms/precise/block-storage-broker) service can automatically handle attaching the volume and mounting it to the unit before MongoDB is setup to use it.

For example if you've created the volumes `vol-id-00001` and `vol-id-00002` and want to attach them to your 2 mongo units, with your OpenStack or AWS credentials in a `credential.yaml` file:

    juju deploy block-storage-broker --config credentials.yaml
    juju deploy storage
    juju add-relation block-storage-broker storage
    juju set storage provider=block-storage-broker
    juju set volume_map="{mongodb/0: vol-id-00001, mongodb/1: vol-id-00002}"
    juju add-relation storage mongodb


### Use a permanent Openstack volume to store mongodb data. (DEPRECATED)

**Note**: Although these steps will still work they are now deprecated, you should use the storage subordinate above instead.

To deploy mongodb using permanent volume on Openstack, the permanent volume should be attached to the mongodb unit just after the deployment, then the configuration should be updated like follows.

    juju set mongodb volume-dev-regexp="/dev/vdc" volume-map='{"mongodb/0": "vol-id-00000000000000"}' volume-ephemeral-storage=false

### Backups

Backups can be enabled via config. Note that destroying the service cannot
currently remove the backup cron job so it will continue to run. There is a
setting for the number of backups to keep, however, to prevent from filling
disk space.

To fetch the backups scp the files down from the path in the config.

### Benchmarking

Mongo units can be benchmarked via the `perf` juju action, available beginning with juju 1.23.

    $ juju action defined mongodb
    perf: The standard mongoperf benchmark.
    $ juju action do mongodb/0 perf
    Action queued with id: 23532149-15c2-47f0-8d97-115fb7dfa1cd
    $ juju action fetch --wait 0 23532149-15c2-47f0-8d97-115fb7dfa1cd
    results:
      meta:
        composite:
          direction: desc
          units: ops/sec
          value: "7736507.70391"
        start: 2015-05-07T16:36:04Z
        stop: 2015-05-07T16:39:05Z
      results:
        average:
          units: ops/sec
          value: "7736507.70391"
        iterations:
          units: iterations
          value: "179"
        max:
          units: ops/sec
          value: "10282496"
        min:
          units: ops/sec
          value: "3874546"
        total:
          units: ops
          value: "1384834879"
    status: completed
    timing:
      completed: 2015-05-07 16:39:06 +0000 UTC
      enqueued: 2015-05-07 16:36:01 +0000 UTC
      started: 2015-05-07 16:36:04 +0000 UTC

## Known Limitations and Issues

- If your master/slave/replicaset deployment is not updating correctly, check the log files at `/var/log/mongodb/mongodb.log` to see if there is an obvious reason ( port not open etc.).
- Ensure that TCP port 27017 is accessible from all of the nodes in the deployment.
- If you are trying to access your MongoDB instance from outside your deployment, ensure that the service has been exposed ( `juju expose mongodb` )
- Make sure that the mongod process is running ( ps -ef | grep mongo ).
- Try restarting the database ( restart mongodb )
- If all else fails, remove the data directory on the slave ( `rm -fr /var/log/mongodb/data/*` ) and restart the mongodb-slave daemon ( `restart mongodb` ).

# Contact Information

## MongoDB Contact Information

- [MongoDB website](http://mongodb.org)
- [MongoDB documentation](http://www.mongodb.org/display/DOCS/Home)
- [MongoDB bug tracker](https://jira.mongodb.org/secure/Dashboard.jspa)
- [MongoDB user mailing list](https://groups.google.com/forum/#!forum/mongodb-user)
