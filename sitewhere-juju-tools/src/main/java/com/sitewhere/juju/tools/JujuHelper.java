/*
 * Copyright (c) SiteWhere, LLC. All rights reserved. http://www.sitewhere.com
 *
 * The software in this package is published under the terms of the CPAL v1.0
 * license, a copy of which has been included with this distribution in the
 * LICENSE.txt file.
 */
package com.sitewhere.juju.tools;

import java.io.File;
import java.io.InputStreamReader;
import java.net.URL;
import java.net.URLConnection;
import java.util.List;
import java.util.Properties;

import org.dom4j.Document;
import org.dom4j.Element;
import org.dom4j.Namespace;
import org.dom4j.QName;
import org.dom4j.io.SAXReader;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.sitewhere.juju.tools.configuration.DatastoreConfiguration;
import com.sitewhere.juju.tools.configuration.MongoConfiguration;
import com.sitewhere.juju.tools.configuration.MqttConfiguration;
import com.sitewhere.juju.tools.configuration.ProtocolsConfiguration;
import com.sitewhere.juju.tools.configuration.SiteWhereConfiguration;

/**
 * Helper class used by Juju charm scripts to interact with SiteWhere.
 * 
 * @author Derek
 */
public class JujuHelper {

	/** SiteWhere CE namespace */
	public static final Namespace SITEWHERE_NS = new Namespace("sw",
			"http://www.sitewhere.com/schema/sitewhere/ce");

	/** SiteWhere base path */
	public static final String SITEWHERE_BASE = "/opt/sitewhere/";

	/** SiteWhere configuration file base path */
	public static final String SITEWHERE_CONFIG_BASE = SITEWHERE_BASE + "conf/sitewhere/";

	/** SiteWhere configuration file location */
	public static final String SITEWHERE_CONFIG = SITEWHERE_CONFIG_BASE + "sitewhere-server.xml";

	/** SiteWhere state information */
	public static final String SITEWHERE_STATE = SITEWHERE_BASE + "sitewhere.state";

	/** MongoDB state information */
	public static final String MONGO_STATE = SITEWHERE_BASE + "mongo.state";

	/** MQTT state information */
	public static final String MQTT_STATE = SITEWHERE_BASE + "mqtt.state";

	/** SiteWhere Load Test configuration file base path */
	public static final String SITEWHERE_LOAD_TEST_BASE = SITEWHERE_BASE + "conf/loadtest/";

	/** SiteWhere Load Test configuration file location */
	public static final String SITEWHERE_LOAD_TEST_CONFIG = SITEWHERE_LOAD_TEST_BASE
			+ "sitewhere-loadtest.xml";

	public static void main(String[] args) {
		if (args.length < 1) {
			System.err.println("No command argument passed.");
			System.exit(1);
		}
		try {
			Command command = Command.getCommand(args[0]);
			switch (command) {
			case SiteWhereState: {
				echoSiteWhereState(args);
				break;
			}
			case MongoState: {
				echoMongoState(args);
				break;
			}
			case MQTTState: {
				echoMQTTState(args);
				break;
			}
			case BuildConfigurationProperties: {
				buildConfigurationProperties(args);
				break;
			}
			case LoadRemoteConfiguration: {
				loadRemoteConfiguration(args);
				break;
			}
			}
		} catch (Exception e) {
			System.err.println("Invalid command argument passed: " + args[0]);
			System.exit(1);
		}
	}

	/**
	 * Echo SiteWhere confiuration state to standard out.
	 * 
	 * @param args
	 */
	protected static void echoSiteWhereState(String[] args) {
		SiteWhereConfiguration state = new SiteWhereConfiguration();
		try {
			Document sitewhere = getSiteWhereXmlDOM();

			DatastoreConfiguration dsState = new DatastoreConfiguration();
			dsState.setMongoConfigured(checkMongo(sitewhere));
			dsState.setHbaseConfigured(checkHBase(sitewhere));
			state.setDatastoreConfiguration(dsState);

			ProtocolsConfiguration proto = new ProtocolsConfiguration();
			proto.setUsesMqtt(checkMQTT(sitewhere));
			state.setProtocolsConfiguration(proto);
		} catch (Exception e) {
			state.setError("ERROR: " + e.getMessage());
		} finally {
			ObjectMapper mapper = new ObjectMapper();
			mapper.enable(SerializationFeature.INDENT_OUTPUT);
			try {
				System.out.println(mapper.writeValueAsString(state));
			} catch (JsonProcessingException e) {
				System.out.println("{ \"error\": \"Unable to marshal server configuration state.\" }");
			}
		}
	}

	/**
	 * Echo MongoDB configuration state to standard out.
	 * 
	 * @param args
	 */
	protected static void echoMongoState(String[] args) {
		if (args.length < 3) {
			System.err.println("Not enough arguments passed for MongoDB configuration.");
			System.exit(1);
		}
		MongoConfiguration mongo = new MongoConfiguration();
		mongo.setHostname(args[1]);
		mongo.setPort(Integer.parseInt(args[2]));

		ObjectMapper mapper = new ObjectMapper();
		mapper.enable(SerializationFeature.INDENT_OUTPUT);
		try {
			System.out.println(mapper.writeValueAsString(mongo));
		} catch (JsonProcessingException e) {
			System.out.println("{ \"error\": \"Unable to marshal MongoDB configuration state.\" }");
		}
	}

	/**
	 * Echo MQTT configuration state to standard out.
	 * 
	 * @param args
	 */
	protected static void echoMQTTState(String[] args) {
		if (args.length < 3) {
			System.err.println("Not enough arguments passed for MQTT configuration.");
			System.exit(1);
		}
		MqttConfiguration mqtt = new MqttConfiguration();
		mqtt.setHostname(args[1]);
		mqtt.setPort(Integer.parseInt(args[2]));

		ObjectMapper mapper = new ObjectMapper();
		mapper.enable(SerializationFeature.INDENT_OUTPUT);
		try {
			System.out.println(mapper.writeValueAsString(mqtt));
		} catch (JsonProcessingException e) {
			System.out.println("{ \"error\": \"Unable to marshal MQTT configuration state.\" }");
		}
	}

	/**
	 * Build the sitewhere.properties file based on current configuration.
	 * 
	 * @param args
	 */
	protected static void buildConfigurationProperties(String[] args) {
		try {
			ObjectMapper mapper = new ObjectMapper();

			Properties props = new Properties();

			File fSiteWhereState = new File(SITEWHERE_STATE);
			if (!fSiteWhereState.exists()) {
				System.err.println("SiteWhere configuration state file not found.");
				System.exit(1);
			}
			SiteWhereConfiguration sitewhere =
					mapper.readValue(fSiteWhereState, SiteWhereConfiguration.class);
			if (sitewhere.getDatastoreConfiguration().isMongoConfigured()) {
				File fMongoState = new File(MONGO_STATE);
				if (!fMongoState.exists()) {
					System.err.println("SiteWhere MongoDB state file not found.");
					System.exit(1);
				}
				MongoConfiguration mongo = mapper.readValue(fMongoState, MongoConfiguration.class);
				props.put("mongodb.hostname", mongo.getHostname());
				props.put("mongodb.port", String.valueOf(mongo.getPort()));
			}
			if (sitewhere.getProtocolsConfiguration().isUsesMqtt()) {
				File fMqttState = new File(MQTT_STATE);
				if (!fMqttState.exists()) {
					System.err.println("SiteWhere MQTT state file not found.");
					System.exit(1);
				}
				MqttConfiguration mqtt = mapper.readValue(fMqttState, MqttConfiguration.class);
				props.put("mqtt.hostname", mqtt.getHostname());
				props.put("mqtt.port", String.valueOf(mqtt.getPort()));
			}

			props.store(System.out,
					"SiteWhere properties. Generated automatically based on Juju configuration.");
		} catch (Exception e) {
			System.err.println("Unable to generate SiteWhere configuration properties. " + e.getMessage());
			System.exit(1);
		}
	}

	/**
	 * Loads a remote file from a URL and writes it to stdout.
	 * 
	 * @param args
	 */
	protected static void loadRemoteConfiguration(String[] args) {
		if (args.length < 2) {
			System.err.println("No URL provided for loading remote configuration.");
			System.exit(1);
		}
		try {
			URL url = new URL(args[1]);
			URLConnection connection = url.openConnection();
			InputStreamReader reader = new InputStreamReader(connection.getInputStream());
			int data;
			while ((data = reader.read()) != -1) {
				System.out.write(data);
			}
			reader.close();
			System.out.flush();
		} catch (Exception e) {
			System.err.println("Unable to load remote configuration from: " + args[1] + ". " + e.getMessage());
			System.exit(1);
		}
	}

	/**
	 * Check whether MongoDB is configured in the sitewhere-server.xml file.
	 * 
	 * @param sitewhere
	 * @return
	 * @throws Exception
	 */
	protected static boolean checkMongo(Document sitewhere) throws Exception {
		Element ds = getDatastoresElement(sitewhere);
		Element mongo = ds.element(new QName("mongo-datastore", SITEWHERE_NS));
		if (mongo == null) {
			return false;
		} else {
			return true;
		}
	}

	/**
	 * Check whether HBase is configured in the sitewhere-server.xml file.
	 * 
	 * @param sitewhere
	 * @return
	 * @throws Exception
	 */
	protected static boolean checkHBase(Document sitewhere) throws Exception {
		Element ds = getDatastoresElement(sitewhere);
		Element mongo = ds.element(new QName("hbase-datastore", SITEWHERE_NS));
		if (mongo == null) {
			return false;
		} else {
			return true;
		}
	}

	/**
	 * Check whether elements that use MQTT are found.
	 * 
	 * @param sitewhere
	 * @return
	 * @throws Exception
	 */
	protected static boolean checkMQTT(Document sitewhere) throws Exception {
		Element sources = getEventSourcesElement(sitewhere);
		List<?> mqttSources = sources.elements(new QName("mqtt-event-source", SITEWHERE_NS));
		if (mqttSources.size() > 0) {
			return true;
		}

		Element dests = getCommandDestinationsElement(sitewhere);
		if (dests != null) {
			List<?> mqttDests = dests.elements(new QName("mqtt-command-destination", SITEWHERE_NS));
			if (mqttDests.size() > 0) {
				return true;
			}
		}

		return false;
	}

	/**
	 * Get the SiteWhere event sources element from sitewhere-server.xml.
	 * 
	 * @param sitewhere
	 * @return
	 * @throws Exception
	 */
	protected static Element getEventSourcesElement(Document sitewhere) throws Exception {
		Element devcomm = getDeviceCommunicationElement(sitewhere);

		Element sources = devcomm.element(new QName("event-sources", SITEWHERE_NS));
		if (sources == null) {
			throw new Exception("Event sources section not found.");
		}
		return sources;
	}

	/**
	 * Get the SiteWhere command destinations element from sitewhere-server.xml. Section
	 * is optiional, so result may be null.
	 * 
	 * @param sitewhere
	 * @return
	 * @throws Exception
	 */
	protected static Element getCommandDestinationsElement(Document sitewhere) throws Exception {
		Element devcomm = getDeviceCommunicationElement(sitewhere);

		return devcomm.element(new QName("command-destinations", SITEWHERE_NS));
	}

	/**
	 * Get the SiteWhere device commuication element from sitewhere-server.xml.
	 * 
	 * @param sitewhere
	 * @return
	 * @throws Exception
	 */
	protected static Element getDeviceCommunicationElement(Document sitewhere) throws Exception {
		Element configuration = getConfigurationElement(sitewhere);

		Element devcomm = configuration.element(new QName("device-communication", SITEWHERE_NS));
		if (devcomm == null) {
			throw new Exception("Device communication section not found.");
		}
		return devcomm;
	}

	/**
	 * Get the SiteWhere datastore element from sitewhere-server.xml.
	 * 
	 * @param sitewhere
	 * @return
	 * @throws Exception
	 */
	protected static Element getDatastoresElement(Document sitewhere) throws Exception {
		Element configuration = getConfigurationElement(sitewhere);

		Element datastores = configuration.element(new QName("datastore", SITEWHERE_NS));
		if (datastores == null) {
			throw new Exception("Datastore section not found.");
		}
		return datastores;
	}

	/**
	 * Get the SiteWhere configuration element from sitewhere-server.xml.
	 * 
	 * @param sitewhere
	 * @return
	 * @throws Exception
	 */
	protected static Element getConfigurationElement(Document sitewhere) throws Exception {
		Element beans = sitewhere.getRootElement();

		Element configuration = beans.element(new QName("configuration", SITEWHERE_NS));
		if (configuration == null) {
			throw new Exception("Configuration element not found.");
		}
		return configuration;
	}

	/**
	 * Load sitewhere-server.xml as a DOM document.
	 * 
	 * @return
	 * @throws Exception
	 */
	protected static Document getSiteWhereXmlDOM() throws Exception {
		SAXReader reader = new SAXReader();
		File sitewhere = new File(SITEWHERE_CONFIG);
		return reader.read(sitewhere);
	}

	/**
	 * Load sitewhere-server.xml as a DOM document.
	 * 
	 * @return
	 * @throws Exception
	 */
	protected static Document getLoadTestXmlDOM() throws Exception {
		SAXReader reader = new SAXReader();
		File sitewhere = new File(SITEWHERE_CONFIG);
		return reader.read(sitewhere);
	}

	/**
	 * Enumerates commands available.
	 * 
	 * @author Derek
	 */
	private enum Command {

		/** Capture SiteWhere state and send JSON to system out */
		SiteWhereState("sitewhereState"),

		/** Capture MongoDB state and send JSON to system out */
		MongoState("mongoState"),

		/** Capture MQTT state and send JSON to system out */
		MQTTState("mqttState"),

		/** Build properties file based on configuration */
		BuildConfigurationProperties("buildProperties"),

		/** Load a remote configuration file to stdout */
		LoadRemoteConfiguration("loadRemoteConfig");

		/** Command string */
		private String command;

		private Command(String command) {
			this.command = command;
		}

		public String getCommand() {
			return command;
		}

		public static Command getCommand(String value) throws Exception {
			for (Command command : Command.values()) {
				if (command.getCommand().equals(value)) {
					return command;
				}
			}
			throw new Exception("Unknown command: " + value);
		}
	}
}