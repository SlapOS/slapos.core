portal = context.getPortalObject()

if context.getRole() == "host":
  reference_prefix = "SITE"
else:
  reference_prefix = "O"

reference = "%s-%s" % (reference_prefix, portal.portal_ids.generateNewId(
    id_group='slap_organisation_reference',
    id_generator='uid'))

context.edit(reference=reference)
