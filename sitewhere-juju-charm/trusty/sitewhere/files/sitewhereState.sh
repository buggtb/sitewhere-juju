/usr/bin/java -jar /opt/sitewhere/juju-tools.jar sitewhereState > /opt/sitewhere/sitewhere.state
if [ $? -ne 0 ]; then
  juju-log "Unable to run SiteWhere Java state extraction command."
  exit 1
fi

sw_err=$(cat /opt/sitewhere/sitewhere.state | jq '.error')
if [ "$sw_err" != "null" ]; then
  juju-log "Error inspecting SiteWhere configuration file."
  juju-log $sw_err
  exit 1
fi

