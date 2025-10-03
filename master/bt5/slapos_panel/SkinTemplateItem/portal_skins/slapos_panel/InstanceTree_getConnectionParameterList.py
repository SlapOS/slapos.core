result = []
instance = context.InstanceTree_getRootInstance()

if instance is not None:
  result = instance.SoftwareInstance_getConnectionParameterList(
               relative_url=context.getRelativeUrl(), raw=raw)

return result
