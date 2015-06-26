/*
 * Copyright (c) SiteWhere, LLC. All rights reserved. http://www.sitewhere.com
 *
 * The software in this package is published under the terms of the CPAL v1.0
 * license, a copy of which has been included with this distribution in the
 * LICENSE.txt file.
 */
package com.sitewhere.juju.tools.configuration;

/**
 * Used to indicate which datastore is configured.
 * 
 * @author Derek
 */
public class DatastoreConfiguration {

	/** Indicates if MongoDB is configured */
	private boolean mongoConfigured;

	/** Indicates if HBase is configured */
	private boolean hbaseConfigured;

	public boolean isMongoConfigured() {
		return mongoConfigured;
	}

	public void setMongoConfigured(boolean mongoConfigured) {
		this.mongoConfigured = mongoConfigured;
	}

	public boolean isHbaseConfigured() {
		return hbaseConfigured;
	}

	public void setHbaseConfigured(boolean hbaseConfigured) {
		this.hbaseConfigured = hbaseConfigured;
	}
}