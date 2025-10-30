from DateTime import DateTime
from Products.ZSQLCatalog.SQLCatalog import Query, NegatedQuery
from erp5.component.module.DateUtils import addToDate

portal = context.getPortalObject()
limit_date = addToDate(DateTime(), dict(month=-1))
portal.portal_catalog.searchAndActivate(
      portal_type="Support Request",
      simulation_state="suspended",
      strict_resource_uid=NegatedQuery(Query(strict_resource_uid=portal.service_module.slapos_crm_monitoring.getUid())),
      modification_date="<%s" % limit_date,
      method_id='SupportRequest_closeIfInactiveForAMonth',
      method_kw={"activate_kw": {'tag': tag, 'priority': 2}},
      activate_kw={'tag': tag, 'priority': 2}
      )
context.activate(after_tag=tag).getId()
