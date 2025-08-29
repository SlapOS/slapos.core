from Products.ZSQLCatalog.SQLCatalog import SimpleQuery
from erp5.component.module.DateUtils import addToDate

portal = context.getPortalObject()
activate_kw = {'tag': tag, 'priority': 5}

portal.portal_catalog.searchAndActivate(
  portal_type='Project',
  # check old enough projects, to give user some time to configure it
  creation_date=SimpleQuery(
    creation_date=addToDate(DateTime(), to_add={'day': -30}),
    comparison_operator="<"
  ),
  validation_state='validated',

  method_id='Project_checkForGarbageCollect',
  method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw
)

context.activate(after_tag=tag).getId()
