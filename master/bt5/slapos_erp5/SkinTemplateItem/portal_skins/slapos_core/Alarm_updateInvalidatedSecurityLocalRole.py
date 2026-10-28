from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, ComplexQuery
portal = context.getPortalObject()

base_tag = tag

portal_type_list = ('Remote Node', 'Software Instance', 'Visit',
  'Software Product', 'Note', 'Assignment Request', 'Sale Trade Condition',
  'Support Request', 'Allocation Supply', 'Instance Tree', 'Letter',
  'Acknowledgement', 'Compute Node', 'Upgrade Decision', 'Invitation Token',
  'Mail Message', 'Web Message', 'Computer Model', 'Short Message',
  'Computer Network', 'Instance Node', 'Fax Message', 'Sale Supply',
  'Software Installation', 'Slave Instance', 'Site Message', 'Phone Call')

# project_security_uid update
portal.portal_catalog.searchAndActivate(
  portal_type=portal_type_list,
  project_security_uid='%',
  activate_kw={'tag': tag, 'priority': 5},
  query=ComplexQuery(
    SimpleQuery(follow_up__validation_state='invalidated'),
    SimpleQuery(source_project__validation_state='invalidated'),
    SimpleQuery(destination_project__validation_state='invalidated'),
  logical_operator="OR"),
  method_id='updateLocalRolesOnSecurityGroups'
)

after_tag = tag
tag = "%s-certificate-login" % (base_tag)

portal.portal_catalog.searchAndActivate(
  portal_type='Certificate Login',
  project_security_uid='%',
  activate_kw={'tag': tag, 'after_tag': after_tag, 'priority': 5},
  parent_follow_up__portal_type='Project',
  parent_follow_up__validation_state='invalidated',
  method_id='updateLocalRolesOnSecurityGroups'
)


after_tag = tag
tag = "%s-software-installation" % (base_tag)

# computer_security_uid update
portal.portal_catalog.searchAndActivate(
  portal_type="Software Installation",
  computer_security_uid='%',
  activate_kw={'tag': tag, 'after_tag': after_tag, 'priority': 5},
  aggregate__portal_type=['Compute Node', 'Remote Node', 'Instance Node'],
  aggregate__validation_state='invalidated',
  method_id='updateLocalRolesOnSecurityGroups'
)

after_tag = tag
tag = "%s-instance" % (base_tag)

portal.portal_catalog.searchAndActivate(
  portal_type=["Software Instance", "Slave Instance"],
  activate_kw={'tag': tag, 'after_tag': after_tag, 'priority': 5},
  computer_security_uid='%',
  aggregate_parent_validation_state='invalidated',
  method_id='updateLocalRolesOnSecurityGroups'
)

context.activate(after_tag=tag).getId()
