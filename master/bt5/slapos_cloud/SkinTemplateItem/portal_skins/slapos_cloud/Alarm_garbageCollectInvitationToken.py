from Products.ZSQLCatalog.SQLCatalog import Query
from erp5.component.module.DateUtils import addToDate
from DateTime import DateTime

portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type="Invitation Token",
  validation_state="validated",
  creation_date=Query(creation_date=addToDate(DateTime(), to_add={'day': -7}), range="max"),
  method_id='invalidate',
  method_kw={"comment": "Unused for 7 days."},
  activate_kw={'tag': tag},
)

context.activate(after_tag=tag).getId()
