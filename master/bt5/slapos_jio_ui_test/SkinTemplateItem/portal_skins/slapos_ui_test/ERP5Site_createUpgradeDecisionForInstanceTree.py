portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

# Find user Software installation
instance_tree = portal.portal_catalog.getResultValue(
  portal_type='Instance Tree',
  validation_state='validated',
  default_destination_section_uid=person.getUid()
)

software_release = portal.portal_catalog.getResultValue(
  portal_type='Software Release',
  url_string=instance_tree.getUrlString(),
  validation_state=['validated', 'published', 'published_alive']
)

new_software_release = portal.software_release_module.newContent(
  portal_type='Software Release',
  url_string=software_release.getUrlString() + ".newerversion",
  reference="test-1.99.9999",
  version="1.99.9999",
  language="en",
  destination_section=person.getRelativeUrl(),
  effective_date=DateTime())

new_software_release.publishAlive()

instance_tree.setUpgradeScope("ask_confirmation")

return portal.ERP5Site_createFakeUpgradeDecision(
  new_software_release, instance_tree)
