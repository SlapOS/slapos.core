return {
  'url': 'https://monitor.app.officejs.com/#/?page=ojsm_landing'
}
# TODO how to get from a global param or context so hardcode is avoided?
# from context.InstanceTree_getConnectionParameterList(raw=True): ?
# instance.getConnectionXmlAsDict() ?

if context.getPortalType() == "Instance Tree":
  instance_tree = context
if context.getPortalType() in ["Software Instance", "Slave Instance"]:
  instance_tree = context.getSpecialise()

dict = instance_tree.InstanceTree_getMonitorParameterDict()
