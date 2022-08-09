portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

# Find user Software installation
software_installation = portal.portal_catalog.getResultValue(
  portal_type='Software Installation',
  validation_state='validated',
  default_destination_section_uid=person.getUid()
)

software_release = portal.portal_catalog.getResultValue(
  portal_type='Software Release',
  url_string=software_installation.getUrlString(),
  validation_state=['validated', 'published', 'published_alive']
)

new_software_release = portal.software_release_module.newContent(
  portal_type='Software Release',
  url_string=software_release.getUrlString() + ".newerversion",
  reference="test-1.99.9999",
  version="1.99.9999",
  language="en",
  effective_date=DateTime())

new_software_release.publishAlive()

compute_node = software_installation.getAggregateValue()
compute_node.setUpgradeScope("ask_confirmation")

return portal.ERP5Site_createFakeUpgradeDecision(
  new_software_release, compute_node)
