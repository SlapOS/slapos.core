resource_uid = context.service_module.cpu_load_percent.getUid()

return context.InstanceTree_getStatForResource(resource_uid, **kw)
