/usr/bin/java -jar /opt/loadtest/juju-tools.jar loadtestState > /opt/loadtest/loadtest.state
if [ $? -ne 0 ]; then
  juju-log "Unable to run state extraction command."
  exit 1
fi

sw_err=$(cat /opt/loadtest/loadtest.state | jq '.error')
if [ "$sw_err" != "null" ]; then
  juju-log "Error inspecting configuration file."
  juju-log $sw_err
  exit 1
fi

