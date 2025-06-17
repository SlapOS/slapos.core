from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, NegatedQuery


portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  parent_uid=portal.software_instance_module.getUid(),
  validation_state='validated',
  default_aggregate_uid  = NegatedQuery(SimpleQuery(default_aggregate_uid=None)),
  method_id='SoftwareInstance_generateConsumptionDelivery',
  packet_size=1,
  activate_kw={'tag': tag}
)

context.activate(after_tag=tag).getId()
