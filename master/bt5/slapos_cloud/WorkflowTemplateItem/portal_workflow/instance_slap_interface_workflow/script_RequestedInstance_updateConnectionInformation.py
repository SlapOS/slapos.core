instance = state_change['object']

# Raise TypeError if all parameters are not provided
try:
  connection_xml = state_change.kwargs['connection_xml']
except KeyError:
  raise TypeError("RequestedInstance_updateConnectionInformation takes exactly 1 arguments")

edit_kw = {
  'connection_xml': connection_xml,
}

instance.edit(**edit_kw)
# Prevent storing broken XML in text content (which prevent to update parameters after)
context.script_Instance_checkConsistency(state_change)

instance.setLastData(connection_xml)
