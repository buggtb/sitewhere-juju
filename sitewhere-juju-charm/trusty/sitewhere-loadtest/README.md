# Overview

This charm deploys a [SiteWhere](http://www.sitewhere.org) Load Test node
which is used to generate traffic for testing SiteWhere performance. Once
a SiteWhere node or cluster has been established, add one or more load
test nodes to start generating traffic. 

# Usage

The SiteWhere Load Test charm allows for the following options:

- **config-url** - Provides an external configuration URL which is used in place
  of the *sitewhere-loadtest.xml* file included in the charm. This configuration file 
  should include property placeholders for settings that can be configured via 
  relationships. See examples below for more information.

# Examples

## Single Sitewhere node with MongoDB, MQTT, and a SiteWhere Load Test node.

    # Deploy the SiteWhere node 
    juju deploy cs:~sitewhere/trusty/sitewhere
    juju deploy cs:~tasdomas/trusty/mosquitto
    juju deploy mongodb
 
    # Add relationships
    juju add-relation sitewhere mongodb
    juju add-relation sitewhere mosquitto

    # Use an externally specified SiteWhere configuration
    juju set sitewhere config-url=https://goo.gl/wqU7Ep

    # Deploy the SiteWhere Load Test node 
    juju deploy cs:~sitewhere/trusty/sitewhere-loadtest
 
    # Add relationships
    juju add-relation sitewhere-loadtest mosquitto
    juju add-relation sitewhere sitewhere-loadtest

    # Use an externally specified SiteWhere Load Test configuration
    juju set sitewhere-loadtest config-url=https://goo.gl/M4rQF3

# Scaling Out

Any number of SiteWhere Load Test nodes may be run in parallel to generate
traffic. If multiple load test configurations are needed, create multiple
services (using different service names in the deploy command) and scale
them independently.

