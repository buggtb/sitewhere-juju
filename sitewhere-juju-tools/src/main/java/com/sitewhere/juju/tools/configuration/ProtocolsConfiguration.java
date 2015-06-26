/*
 * Copyright (c) SiteWhere, LLC. All rights reserved. http://www.sitewhere.com
 *
 * The software in this package is published under the terms of the CPAL v1.0
 * license, a copy of which has been included with this distribution in the
 * LICENSE.txt file.
 */
package com.sitewhere.juju.tools.configuration;

/**
 * Used to indicate which protocols are configured.
 * 
 * @author Derek
 */
public class ProtocolsConfiguration {

	/** Indicates if the MQTT protocol is used */
	private boolean usesMqtt;

	public boolean isUsesMqtt() {
		return usesMqtt;
	}

	public void setUsesMqtt(boolean usesMqtt) {
		this.usesMqtt = usesMqtt;
	}
}