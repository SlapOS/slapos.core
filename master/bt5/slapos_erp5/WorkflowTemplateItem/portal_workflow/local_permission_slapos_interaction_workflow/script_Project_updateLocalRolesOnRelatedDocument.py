project = state_change['object']

from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, ComplexQuery
portal = project.getPortalObject()

portal_type_list = ('Remote Node', 'Software Instance', 'Visit',
  'Software Product', 'Note', 'Assignment Request', 'Sale Trade Condition',
  'Support Request', 'Allocation Supply', 'Instance Tree', 'Letter',
  'Acknowledgement', 'Compute Node', 'Upgrade Decision', 'Invitation Token',
  'Mail Message', 'Web Message', 'Computer Model', 'Short Message',
  'Computer Network', 'Instance Node', 'Fax Message', 'Sale Supply',
  'Software Installation', 'Slave Instance', 'Site Message', 'Phone Call')

portal.portal_catalog.searchAndActivate(
  portal_type=portal_type_list,
  query=ComplexQuery(
    SimpleQuery(follow_up__uid=project.getUid()),
    SimpleQuery(source_project__uid=project.getUid()),
    SimpleQuery(destination_project__uid=project.getUid()),
  logical_operator="OR"),
  method_id='updateLocalRolesOnSecurityGroups'
)

portal.portal_catalog.searchAndActivate(
  portal_type='Certificate Login',
  parent_follow_up__uid=project.getUid(),
  method_id='updateLocalRolesOnSecurityGroups'
)
