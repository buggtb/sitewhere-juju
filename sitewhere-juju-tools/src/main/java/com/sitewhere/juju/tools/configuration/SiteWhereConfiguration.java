/*
 * Copyright (c) SiteWhere, LLC. All rights reserved. http://www.sitewhere.com
 *
 * The software in this package is published under the terms of the CPAL v1.0
 * license, a copy of which has been included with this distribution in the
 * LICENSE.txt file.
 */
package com.sitewhere.juju.tools.configuration;

/**
 * Result ofs introspecting SiteWhere configuration file.
 * 
 * @author Derek
 */
public class SiteWhereConfiguration {

	/** Set if there was an error */
	private String error;

	/** Datastore configuration state */
	private DatastoreConfiguration datastoreConfiguration;

	/** Protocol configuration state */
	private ProtocolsConfiguration protocolsConfiguration;

	public String getError() {
		return error;
	}

	public void setError(String error) {
		this.error = error;
	}

	public DatastoreConfiguration getDatastoreConfiguration() {
		return datastoreConfiguration;
	}

	public void setDatastoreConfiguration(DatastoreConfiguration datastoreConfiguration) {
		this.datastoreConfiguration = datastoreConfiguration;
	}

	public ProtocolsConfiguration getProtocolsConfiguration() {
		return protocolsConfiguration;
	}

	public void setProtocolsConfiguration(ProtocolsConfiguration protocolsConfiguration) {
		this.protocolsConfiguration = protocolsConfiguration;
	}
}