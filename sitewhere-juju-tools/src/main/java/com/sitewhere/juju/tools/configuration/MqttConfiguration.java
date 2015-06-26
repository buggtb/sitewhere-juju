/*
 * Copyright (c) SiteWhere, LLC. All rights reserved. http://www.sitewhere.com
 *
 * The software in this package is published under the terms of the CPAL v1.0
 * license, a copy of which has been included with this distribution in the
 * LICENSE.txt file.
 */
package com.sitewhere.juju.tools.configuration;

/**
 * Wrapper for capturing MQTT configuration parameters in JSON format.
 * 
 * @author Derek
 */
public class MqttConfiguration {

	/** MQTT host name */
	private String hostname;

	/** MQTT port */
	private int port;

	public String getHostname() {
		return hostname;
	}

	public void setHostname(String hostname) {
		this.hostname = hostname;
	}

	public int getPort() {
		return port;
	}

	public void setPort(int port) {
		this.port = port;
	}
}