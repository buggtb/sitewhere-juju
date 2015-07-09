/*
 * Copyright (c) SiteWhere, LLC. All rights reserved. http://www.sitewhere.com
 *
 * The software in this package is published under the terms of the CPAL v1.0
 * license, a copy of which has been included with this distribution in the
 * LICENSE.txt file.
 */
package com.sitewhere.juju.tools.configuration;

/**
 * Result of introspecting SiteWhere Load Test Node configuration file.
 * 
 * @author Derek
 */
public class LoadTestConfiguration {

	/** Set if there was an error */
	private String error;

	/** Protocol configuration state */
	private ProtocolsConfiguration protocolsConfiguration;

	public String getError() {
		return error;
	}

	public void setError(String error) {
		this.error = error;
	}

	public ProtocolsConfiguration getProtocolsConfiguration() {
		return protocolsConfiguration;
	}

	public void setProtocolsConfiguration(ProtocolsConfiguration protocolsConfiguration) {
		this.protocolsConfiguration = protocolsConfiguration;
	}
}