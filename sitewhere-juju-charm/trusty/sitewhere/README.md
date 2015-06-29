# Overview

This charm deploys [SiteWhere](http://www.sitewhere.org) and allows many 
reltionships to be configured such as:

- Persistence to a MongoDB datasource
- Communication via an MQTT broker (tested with Mosquitto)
- Interaction between SiteWhere instances over Hazelcast queue

In the near future, connection to an HBase cluster will also be supported. 

# Usage

The SiteWhere charm allows for the following options:

- **config-url** - Provides an external configuration URL which is used in place
  of the *sitewhere-server.xml* file included in the charm. This configuration file 
  should include property placeholders for settings that can be configured via 
  relationships. See examples below for more information.

# Examples

## Single Node with MongoDB and MQTT Connectivity

    # Deploy the charms
    juju deploy cs:~sitewhere/trusty/sitewhere sitewhere
    juju deploy cs:~tasdomas/trusty/mosquitto
    juju deploy mongodb
 
    # Add relationships
    juju add-relation sitewhere mongodb
    juju add-relation sitewhere mosquitto

    # Use an externally specified configuration
    juju set sitewhere config-url=https://goo.gl/wqU7Ep

# Scaling Out

SiteWhere is intended to scale gracefully from a single node to hundreds of nodes that process
device event data in parallel. In a scale-out scenario, there are generally one or more
processing groups that consist of frontend nodes that are decoding device events
and processor nodes that store and process the events. This is accomplished using
SiteWhere's built-in support for Hazelcast to allow the processing to be partitioned. 

All nodes are deployed using the same charm, only differing in the remote configuration file
that controls which components SiteWhere uses for processing. Frontend nodes are configured to
allow data in one of [many protocols and formats](http://goo.gl/jqYQdP)
to be pulled into the system, converting them into a common format, then forwarding via a Hazelccast
queue to the processor nodes. The processor nodes are configured to read from the Hazelcast 
queue, store events in a big data persistence store, then perform the configued processing steps.

Many processing options are avabilable including complex event processing, forwarding to 
[Apache Solr](http://lucene.apache.org/solr/) for indexing, processing via ESBs such as MuleSoft's 
[AnyPoint](https://www.mulesoft.com/platform/enterprise-integration)  platform, or handing off to
any of the other systems integrated with SiteWhere. The processor nodes pull from the Hazelcast
queue in round-robin fashion, allowing highly parallelized processing.

Below is an example of a frontend node configuration file: 
[Frontend Node Configuration Example](https://raw.githubusercontent.com/sitewhere/sitewhere-juju/master/sitewhere-juju-config/mongodb-frontend-mqtt.xml)

Below is an example of a processing node configuration file: 
[Processing Node Configuration Example](https://raw.githubusercontent.com/sitewhere/sitewhere-juju/master/sitewhere-juju-config/mongodb-worker.xml)

Note that the frontend node forwards inbound events to the Hazecast queue and the processing node
listens on the queue to receive events to process.

# Considerations for Parallel Processing

There are some gotchas that can come in to play when processing is disbursed over many 
processing nodes. When customizing configurations, it is important to note that the ourbound
processing chain for a single node only interacts with the events processed on that node. In
some cases this can lead to undesired results. For instance, in complex event processing 
using Siddhi, the processor examines a live stream of events to look for patterns. When
events are disbursed across many nodes, the patterns are no longer detected. If complex event
processing is desired, the events from all processing nodes should be forwarded to either an
external Siddhi instance, or a single node that is dedicated to complex event processing.
