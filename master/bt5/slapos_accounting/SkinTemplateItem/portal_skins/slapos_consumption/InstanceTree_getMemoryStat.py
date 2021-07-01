resource_uid = context.service_module.memory_used.getUid()

return context.InstanceTree_getStatForResource(resource_uid, **kw)
